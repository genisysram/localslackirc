# localslackirc
# Copyright (C) 2020 Salvo "LtWorf" Tomaselli
#
# localslackirc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# author Salvo "LtWorf" Tomaselli <tiposchi@tiscali.it>

import asyncio
import unittest

from irc import _MENTIONS_REGEXP, _CHANNEL_MENTIONS_REGEXP, _URL_REGEXP, Client, Provider
from slack import Channel, User


class TestTesto(unittest.TestCase):
    def test_url_re(self):
        cases = [
            # String, matched groups
            ('q1://p1|p', None),
            ('Pinnello <q1://p1|p>', ('q1', 'p1', 'p')),
            ('Pinnello <q1://p1|p> asd asd', ('q1', 'p1', 'p')),
            ('<q1://p1|p> asd asd', ('q1', 'p1', 'p')),
            ('<q1://p1|p a|> asd asd', ('q1', 'p1', 'p a|')),
            ('<q1://p1> asd asd', ('q1', 'p1', '')),
        ]

        for url, expected in cases:
            m = _URL_REGEXP.search(url)
            assert m is None if expected is None else m.groups() == expected

class TestMagic(unittest.TestCase):

    def setUp(self):
        class MockClient:
            def __init__(self):
                self.members = set(('0', ))
            async def get_members(self, channels):
                return self.members
            async def get_user_by_name(self, username):
                return User(username, username, None)
            async def get_user(self, id_):
                return User('0', 'LtWorf', None)

        self.mock_client = MockClient()
        self.client = Client(None, self.mock_client, False, True, Provider.SLACK)

    def test_no_replace(self):
        '''
        Check that no substitutions are done on regular strings and nickname in url
        '''
        cases = [
            'ciao',
            'http://LtWorf/',
            'ciao https://link.com/LtWorf',
            'ciao https://link.com/LtWorf?param',
        ]
        dest = Channel('0', '0', None, None)
        for i in cases:
            assert asyncio.run(self.client._addmagic(i, dest)) == i

    def test_regex_cache(self):
        '''
        Check that the regex is cached and invalidated properly
        '''
        return #FIXME there is no cache for now
        asyncio.run(self.client._addmagic('ciao'))
        initial = id(self.client._magic_regex)
        asyncio.run(self.client._addmagic('ciao'))
        assert initial == id(self.client._magic_regex)
        asyncio.run(self.client._addmagic('ciao'))
        assert initial == id(self.client._magic_regex)
        self.mock_client.usernames = ['myself', 'yourself']
        asyncio.run(self.client._addmagic('ciao'))
        assert initial != id(self.client._magic_regex)

    def test_escapes(self):
        dest = User('0', 'LtWorf', None)
        assert asyncio.run(self.client._addmagic('<', dest)) == '&lt;'
        assert asyncio.run(self.client._addmagic('>ciao', dest)) == '&gt;ciao'

    def test_annoyiances(self):
        dest = User('0', 'LtWorf', None)
        asyncio.run(self.client._addmagic('ciao @here', dest)) == 'ciao <!here>'
        asyncio.run(self.client._addmagic('ciao @channel', dest)) == 'ciao <!channel>'
        asyncio.run(self.client._addmagic('ciao @everyone </', dest)) == 'ciao <!everyone> &lt;/'

    def test_mentions(self):
        dest = Channel('0', '0', None, None)
        assert asyncio.run(self.client._addmagic('ciao LtWorf', dest)) == 'ciao <@LtWorf>'
        assert asyncio.run(self.client._addmagic('LtWorf: ciao', dest)) == '<@LtWorf>: ciao'
        assert asyncio.run(self.client._addmagic('LtWorf: ciao LtWorf', dest)) == '<@LtWorf>: ciao <@LtWorf>'
        assert asyncio.run(self.client._addmagic('_LtWorf', dest)) == '_LtWorf'
        assert asyncio.run(self.client._addmagic('LtWorf: http://link/user=LtWorf', dest)) == '<@LtWorf>: http://link/user=LtWorf'
