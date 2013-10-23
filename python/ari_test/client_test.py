#!/usr/bin/env python

import httpretty
import json
import os
import unittest
import urllib
import urlparse
import ari
import requests

BASE_URL = "http://ari.py/ari"
GET = httpretty.GET
PUT = httpretty.PUT
POST = httpretty.POST
DELETE = httpretty.DELETE


def build_url(*args):
    url = BASE_URL
    for arg in args:
        url = urlparse.urljoin(url + '/', arg)
    return url


def serve(method, *args, **kwargs):
    url = build_url(*args)
    if kwargs.get('body') is None and 'status' not in kwargs:
        kwargs['status'] = requests.codes.no_content
    return httpretty.register_uri(method, url, content_type="application/json",
                                  **kwargs)


class ClientTest(unittest.TestCase):
    def test_docs(self):
        fp = urllib.urlopen("http://ari.py/ari/api-docs/resources.json")
        try:
            actual = json.load(fp)
            self.assertEqual(BASE_URL, actual['basePath'])
        finally:
            fp.close()

    def test_empty_listing(self):
        serve(GET, 'channels', body='[]')
        actual = self.uut.channels.list()
        self.assertEqual([], actual)

    def test_one_listing(self):
        serve(GET, 'channels', body='[{"id": "test-channel"}]')
        serve(DELETE, 'channels', 'test-channel')

        actual = self.uut.channels.list()
        self.assertEqual(1, len(actual))
        actual[0].hangup()

    def test_play(self):
        serve(GET, 'channels', 'test-channel', body='{"id": "test-channel"}')
        serve(POST, 'channels', 'test-channel', 'play',
              body='{"id": "test-playback"}')
        serve(DELETE, 'playback', 'test-playback')

        channel = self.uut.channels.get(channelId='test-channel')
        playback = channel.play(media='sound:test-sound')
        playback.stop()

    def test_bad_resource(self):
        try:
            self.uut.i_am_not_a_resource.list()
            self.fail("How did it find that resource?")
        except AttributeError:
            pass

    def test_bad_repo_method(self):
        try:
            self.uut.channels.i_am_not_a_method()
            self.fail("How did it find that method?")
        except AttributeError:
            pass

    def test_bad_object_method(self):
        serve(GET, 'channels', 'test-channel', body='{"id": "test-channel"}')

        try:
            channel = self.uut.channels.get(channelId='test-channel')
            channel.i_am_not_a_method()
            self.fail("How did it find that method?")
        except AttributeError:
            pass

    def test_bad_param(self):
        try:
            self.uut.channels.list(i_am_not_a_param='asdf')
            self.fail("How did it find that param?")
        except TypeError:
            pass

    def test_bad_response(self):
        serve(GET, 'channels', body='{"message": "This is just a test"}',
              status=500)
        try:
            self.uut.channels.list()
            self.fail("Should have thrown an exception")
        except requests.HTTPError as e:
            self.assertEqual(500, e.response.status_code)
            self.assertEqual(
                {"message": "This is just a test"}, e.response.json())

    def test_endpoints(self):
        serve(GET, 'endpoints',
              body='[{"technology": "TEST", "resource": "1234"}]')
        serve(GET, 'endpoints', 'TEST', '1234',
              body='{"technology": "TEST", "resource": "1234"}')

        endpoints = self.uut.endpoints.list()
        self.assertEqual(1, len(endpoints))
        endpoint = endpoints[0].get()
        self.assertEqual('TEST', endpoint.json['technology'])
        self.assertEqual('1234', endpoint.json['resource'])

    def setUp(self):
        super(ClientTest, self).setUp()
        httpretty.enable()
        self.serve_api()
        self.uut = ari.connect('http://ari.py/', 'test', 'test', 'test')

    def tearDown(self):
        super(ClientTest, self).tearDown()
        httpretty.disable()
        httpretty.reset()

    def serve_api(self):
        for filename in os.listdir('sample-api'):
            if filename.endswith('.json'):
                with open(os.path.join('sample-api', filename)) as fp:
                    body = fp.read()
                serve(GET, 'api-docs', filename, body=body)


if __name__ == '__main__':
    unittest.main()
