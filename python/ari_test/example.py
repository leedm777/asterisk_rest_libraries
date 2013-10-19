#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import ari


session_factory = ari.AriBasicAuthFactory('hey', 'peekaboo')
client = ari.Client('localhost', session_factory, apps='hello')


def on_dtmf(channel, event):
    digit = event['digit']
    if digit == '#':
        channel.play(media='sound:goodbye')
        channel.hangup()
    elif digit == '*':
        channel.play(media='sound:asterisk-friend')
    else:
        channel.play(media='sound:digits/%s' % digit)


def on_start(channel, event):
    channel.on_dtmf_received(on_dtmf)
    channel.answer()
    channel.play(media='sound:hello-world')


client.on_stasis_start(on_start)
client.run()
