#
# Copyright (c) 2013, Digium, Inc.
#

"""ARI client library
"""
import client
import urlparse

from swaggerpy.http_client import SynchronousHttpClient

Client = client.Client


def connect(base_url, username, password, apps):
    split = urlparse.urlsplit(base_url)
    http_client = SynchronousHttpClient()
    http_client.set_basic_auth(split.hostname, username, password)
    return Client(base_url, http_client, apps=apps)
