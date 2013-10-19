#
# Copyright (c) 2013, Digium, Inc.
#

import json
import requests
import requests.auth

import swaggerpy.client


class AriBasicAuthFactory(object):
    def __init__(self, username, password):
        self.auth = requests.auth.HTTPBasicAuth(username, password)

    def build_session(self):
        session = requests.Session()
        session.auth = self.auth
        return session


class Channel(object):
    def __init__(self, client, channel_id):
        self.client = client
        self.channel_client = client.swagger.apis.channels
        self.id = channel_id

    def __getattr__(self, item):
        real_fn = getattr(self.channel_client, item)

        def channel_fn(**kwargs):
            return real_fn(self.channel_client, channelId=self.id, **kwargs)

        return channel_fn

    def on_dtmf_received(self, fn):
        def cb(channel, event):
            if event['channel']['id'] == self.id:
                fn(channel, event)
        self.client.on_dtmf_received(cb)


class Client(object):
    def __init__(self, host, session_factory, secure=False, port=None,
                 apps=None):
        scheme = 'http'
        if secure:
            scheme = 'https'
        if port is None:
            if secure:
                port = 8089
            else:
                port = 8088
        url = "%(scheme)s://%(host)s:%(port)d/ari/api-docs/resources.json" % \
              locals()

        self.swagger = swaggerpy.client.SwaggerClient(
            discovery_url=url, session=session_factory.build_session())

        self.event_listeners = {}

        if isinstance(apps, str):
            apps = [apps]
        self.apps = apps or []

    def run(self):
        ws = self.swagger.apis.events.eventWebsocket(app=','.join(self.apps))
        for msg_str in iter(lambda: ws.recv(), None):
            msg_json = json.loads(msg_str)
            for listener in self.event_listeners.get(
                    msg_json.get('type')) or []:
                listener(msg_json)

    def on_event(self, event_type, fn):
        listeners = self.event_listeners.get(event_type)
        if listeners is None:
            listeners = []
            self.event_listeners[event_type] = listeners
        listeners.append(fn)

    def on_stasis_start(self, fn):
        self.on_event('StasisStart',
                      lambda ev: fn(Channel(self, ev['channel']['id']), ev))

    def on_dtmf_received(self, fn):
        self.on_event('ChannelDtmfReceived',
                      lambda ev: fn(Channel(self, ev['channel']['id']), ev))
