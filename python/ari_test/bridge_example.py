#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import ari

session_factory = ari.AriBasicAuthFactory('hey', 'peekaboo')
client = ari.Client('localhost', session_factory, apps='hello')

bridges = [b for b in client.list_bridges() if b['bridge_type'] == 'holding']
if bridges:
    bridge = bridges[0]
    print "Using bridge %s" % bridge.id
else:
    bridge = client.create_bridge(type='holding')
    print "Created bridge %s" % bridge.id


def on_enter(bridge, ev):
    if not ev['channel']['name'].startswith('Announcer/'):
        bridge.play(media="sound:demo-congrats")


bridge.on_event('ChannelEnteredBridge', on_enter)


def add_to_bridge(channel, ev):
    channel.answer()
    bridge.addChannel(channel=channel.id)


client.on_channel_event('StasisStart', add_to_bridge)
client.run()
