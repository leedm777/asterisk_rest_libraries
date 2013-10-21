#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import ari

session_factory = ari.AriBasicAuthFactory('hey', 'peekaboo')
client = ari.Client('localhost', session_factory, apps='hello')

bridges = [b for b in client.list_bridges() if b['bridge_type'] == 'holding']
if bridges:
    holding_bridge = bridges[0]
    print "Using bridge %s" % holding_bridge.id
else:
    holding_bridge = client.create_bridge(type='holding')
    print "Created bridge %s" % holding_bridge.id


def connect(incoming, ev):
    if ev['args'] == ['incoming']:
        incoming.answer()
        incoming.play(media="sound:pls-wait-connect-call")
        holding_bridge.addChannel(channel=incoming.id)
        outgoing = client.originate(endpoint="SIP/blink", app="hello",
                                    appArgs="dialed")
        incoming.on_event('StasisEnd', lambda *args: outgoing.hangup())
        outgoing.on_event('ChannelDestroyed', lambda *args: incoming.hangup())

        def bridge_the_call(*ignored):
            bridge = client.create_bridge(type='mixing')
            outgoing.answer()
            bridge.addChannel(channel=[incoming.id, outgoing.id])
            outgoing.on_event('StasisEnd', lambda *args: bridge.destroy())
        outgoing.on_event('StasisStart', bridge_the_call)


client.on_channel_event('StasisStart', connect)
client.run()
