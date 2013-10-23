#!/usr/bin/env python

import httpretty
import json
import os
import unittest
import urllib
import urlparse
import ari

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
    return httpretty.register_uri(method, url, content_type="application/json",
                                  **kwargs)


class ClientTest(unittest.TestCase):
    def test_docs(self):
        url = "http://ari.py/ari/api-docs/resources.json"
        fp = urllib.urlopen(url)
        try:
            actual = json.load(fp)
            self.assertEqual(BASE_URL, actual['basePath'])
        finally:
            fp.close()

    def test_listing(self):
        serve(GET, 'channels', body='[]')
        actual = self.uut.channels.list()
        self.assertEqual([], actual)

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
