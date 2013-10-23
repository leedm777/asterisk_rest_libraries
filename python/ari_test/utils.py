#!/usr/bin/env python

import httpretty
import os
import unittest
import urlparse
import ari
import requests


class AriTestCase(unittest.TestCase):
    BASE_URL = "http://ari.py/ari"

    def setUp(self):
        super(AriTestCase, self).setUp()
        httpretty.enable()
        self.serve_api()
        self.uut = ari.connect('http://ari.py/', 'test', 'test', 'test')

    def tearDown(self):
        super(AriTestCase, self).tearDown()
        httpretty.disable()
        httpretty.reset()

    def build_url(self, *args):
        url = self.BASE_URL
        for arg in args:
            url = urlparse.urljoin(url + '/', arg)
        return url

    def serve_api(self):
        for filename in os.listdir('sample-api'):
            if filename.endswith('.json'):
                with open(os.path.join('sample-api', filename)) as fp:
                    body = fp.read()
                self.serve(httpretty.GET, 'api-docs', filename, body=body)

    def serve(self, method, *args, **kwargs):
        url = self.build_url(*args)
        if kwargs.get('body') is None and 'status' not in kwargs:
            kwargs['status'] = requests.codes.no_content
        return httpretty.register_uri(method, url,
                                      content_type="application/json",
                                      **kwargs)
