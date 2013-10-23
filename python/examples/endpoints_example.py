#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import ari
import logging

from swaggerpy.http_client import SynchronousHttpClient

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


http_client = SynchronousHttpClient()
http_client.set_basic_auth('localhost', 'hey', 'peekaboo')
client = ari.Client('http://localhost:8088/', http_client, apps='hello')

print "%r" % client.endpoints.list()
