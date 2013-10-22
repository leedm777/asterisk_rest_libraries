#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import logging
import ari

from swaggerpy.http_client import SynchronousHttpClient

logging.basicConfig()

log = logging.getLogger(__name__)

http_client = SynchronousHttpClient()
http_client.set_basic_auth('localhost', 'hey', 'peekaboo')
client = ari.Client('http://localhost:8088/', http_client, apps='hello')


def on_start(channel, event):
    channel.answer()
    playback = channel.play(media='sound:demo-congrats')

    def on_dtmf(channel, event):
        digit = event['digit']
        if digit == '5':
            playback.control(operation='pause')
        elif digit == '8':
            playback.control(operation='unpause')
        elif digit == '4':
            playback.control(operation='reverse')
        elif digit == '6':
            playback.control(operation='forward')
        elif digit == '2':
            playback.control(operation='restart')
        elif digit == '#':
            playback.stop()
        else:
            log.error("Unknown DTMF %s", digit)

    channel.on_event('ChannelDtmfReceived', on_dtmf)


client.on_channel_event('StasisStart', on_start)
client.run()
