#!/usr/bin/env python

import unittest
import ari
import re

from ari_test.utils import AriTestCase
from swaggerpy.http_client import SynchronousHttpClient

BASE_URL = "http://ari.py/ari"


class WebSocketTest(AriTestCase):
    def test_empty(self):
        uut = connect(BASE_URL, 'test', [])
        actual = []
        uut.on_event(re.compile('.*'), lambda ev: actual.append(ev))
        uut.run()
        self.assertEqual([], actual)

    def test_series(self):
        messages = [
            '{"type": "do"}',
            '{"type": "re"}',
            '{"type": "mi"}'
        ]
        uut = connect(BASE_URL, 'test', messages)
        actual = []
        uut.on_event(re.compile('.*'), lambda ev: actual.append(ev))
        uut.run()
        expected = [
            {"type": "do"},
            {"type": "re"},
            {"type": "mi"}
        ]
        self.assertEqual(expected, actual)


class WebSocketStubConnection(object):
    def __init__(self, messages):
        self.messages = list(messages)
        self.messages.reverse()

    def recv(self):
        if self.messages:
            return str(self.messages.pop())
        return None


class WebSocketStubClient(SynchronousHttpClient):
    """Stub WebSocket connection.

    :param messages: List of messages to return.
    :type  messages: list
    """

    def __init__(self, messages):
        super(WebSocketStubClient, self).__init__()
        self.messages = messages

    def ws_connect(self, url, params=None):
        return WebSocketStubConnection(self.messages)


def connect(base_url, apps, messages):
    http_client = WebSocketStubClient(messages)
    return ari.Client(base_url, http_client, apps=apps)


if __name__ == '__main__':
    unittest.main()
