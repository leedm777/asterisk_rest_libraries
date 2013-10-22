#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#
from requests import HTTPError

import ari
from swaggerpy.http_client import SynchronousHttpClient, requests
import logging

logging.basicConfig()

http_client = SynchronousHttpClient()
http_client.set_basic_auth('localhost', 'hey', 'peekaboo')
client = ari.Client('http://localhost:8088/', http_client, apps='hello')

bridges = [b for b in client.bridges.list()
           if b.json['bridge_type'] == 'holding']
if bridges:
    holding_bridge = bridges[0]
    print "Using bridge %s" % holding_bridge.id
else:
    holding_bridge = client.bridges.create(type='holding')
    print "Created bridge %s" % holding_bridge.id


def safe_hangup(channel):
    try:
        channel.hangup()
    except HTTPError as e:
        # Ignore 404's, since channels can go away before we get to them
        if e.response.status_code != requests.codes.not_found:
            raise

def connect(incoming, ev):
    if ev['args'] == ['incoming']:
        incoming.answer()
        incoming.play(media="sound:pls-wait-connect-call")
        holding_bridge.addChannel(channel=incoming.id)
        outgoing = client.channels.originate(endpoint="SIP/blink", app="hello",
                                             appArgs="dialed")
        incoming.on_event('StasisEnd', lambda *args: safe_hangup(outgoing))
        outgoing.on_event('ChannelDestroyed', lambda *args: safe_hangup(incoming))

        def bridge_the_call(*ignored):
            bridge = client.bridges.create(type='mixing')
            outgoing.answer()
            bridge.addChannel(channel=[incoming.id, outgoing.id])
            outgoing.on_event('StasisEnd', lambda *args: bridge.destroy())

        outgoing.on_event('StasisStart', bridge_the_call)


client.on_channel_event('StasisStart', connect)
client.run()
