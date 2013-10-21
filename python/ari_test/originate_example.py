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


def on_enter(bridge, ev):
    # ignore announcer channels - see ASTERISK-22744
    if ev['channel']['name'].startswith('Announcer/'):
        return


class Call(object):
    def __init__(self, incoming, outgoing):
        self.incoming_id = incoming.id
        self.outgoing_id = outgoing.id
        self.bridge_id = None


calls = []


def hold_please(channel, ev):
    if ev['args'] == ['dialed']:
        call = [c for c in calls if c.outgoing_id == channel.id]
        if len(call) != 1:
            channel.hangup()
            return
        call = call[0]
        channel.answer()
        bridge = client.create_bridge(type='mixing')
        call.bridge_id = bridge.id
        bridge.addChannel(channel=[call.incoming_id, call.outgoing_id])
    else:
        channel.answer()
        channel.play(media="sound:pls-wait-connect-call")
        holding_bridge.addChannel(channel=channel.id)
        dialed = client.originate(endpoint="SIP/blink", app="hello",
                                  appArgs="dialed")
        calls.append(Call(channel, dialed))


def bye(channel, ev):
    for call in calls:
        if channel.id == call.incoming_id:
            client.swagger.apis.channels.hangup(channelId=call.outgoing_id)
        elif channel.id == call.outgoing_id:
            client.swagger.apis.channels.hangup(channelId=call.incoming_id)
        else:
            continue

        client.swagger.apis.bridges.destroy(bridgeId=call.bridge_id)


client.on_channel_event('StasisStart', hold_please)
client.on_channel_event('StasisEnd', bye)
client.on_channel_event('ChannelDestroyed', bye)
client.run()
