#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import ari
from swaggerpy.http_client import SynchronousHttpClient

http_client = SynchronousHttpClient()
http_client.set_basic_auth('localhost', 'hey', 'peekaboo')
client = ari.Client('http://localhost:8088/', http_client, apps='hello')

bridges = [b for b in client.bridges.list() if b.json['bridge_type'] == 'holding']
if bridges:
    bridge = bridges[0]
    print "Using bridge %s" % bridge.id
else:
    bridge = client.bridges.create(type='holding')
    print "Created bridge %s" % bridge.id


def on_enter(bridge, ev):
    # ignore announcer channels - see ASTERISK-22744
    if not ev['channel']['name'].startswith('Announcer/'):
        bridge.play(media="sound:hello-world")


bridge.on_event('ChannelEnteredBridge', on_enter)


def add_to_bridge(channel, ev):
    channel.answer()
    bridge.addChannel(channel=channel.id)


client.on_channel_event('StasisStart', add_to_bridge)
client.run()
