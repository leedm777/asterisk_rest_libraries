#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import ari
from swaggerpy.http_client import SynchronousHttpClient

http_client = SynchronousHttpClient()
http_client.set_basic_auth('localhost', 'hey', 'peekaboo')
client = ari.Client('http://localhost:8088/', http_client, apps='hello')


def on_dtmf(channel, event):
    digit = event['digit']
    if digit == '#':
        channel.play(media='sound:goodbye')
        channel.continueInDialplan()
    elif digit == '*':
        channel.play(media='sound:asterisk-friend')
    else:
        channel.play(media='sound:digits/%s' % digit)


def on_start(channel, event):
    channel.on_event('ChannelDtmfReceived', on_dtmf)
    channel.answer()
    channel.play(media='sound:hello-world')


client.on_channel_event('StasisStart', on_start)
client.run()
