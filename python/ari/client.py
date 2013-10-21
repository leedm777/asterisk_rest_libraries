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
    def __init__(self, client, channel_json):
        self.client = client
        self.channel_client = client.swagger.apis.channels
        self.channel_json = channel_json
        self.id = channel_json['id']

    def __getattr__(self, item):
        real_fn = getattr(self.channel_client, item)
        if not hasattr(real_fn, '__call__'):
            raise AttributeError(
                "'%s' object has no attribute '%r'" % (
                    self.__class__.__name__, item))

        def channel_fn(**kwargs):
            return real_fn(self.channel_client, channelId=self.id, **kwargs)

        return channel_fn

    def on_event(self, event_type, fn):
        def fn_filter(channels, event):
            if isinstance(channels, dict):
                if self.id in [c.id for c in channels.values()]:
                    fn(channels, event)
            else:
                if self.id == channels.id:
                    fn(channels, event)

        self.client.on_channel_event(event_type, fn_filter)


class Bridge(object):
    pass


class Playback(object):
    pass


class Client(object):
    def __init__(self, host, session_factory, secure=False, port=None,
                 apps=None):
        scheme = 'http'
        default_port = 8088
        if secure:
            scheme = 'https'
            default_port = 8089
        if port is None:
            port = default_port

        url = "%(scheme)s://%(host)s:%(port)d/ari/api-docs/resources.json" % \
              locals()

        self.swagger = swaggerpy.client.SwaggerClient(
            discovery_url=url, session=session_factory.build_session())

        events = [api.api_declaration
                  for api in self.swagger.api_docs.apis
                  if api.name == 'events']
        if events:
            self.event_models = events[0].models
        else:
            self.event_models = {}

        self.event_listeners = {}

        if isinstance(apps, str):
            apps = [apps]
        self.apps = apps or []

    def run(self):
        ws = self.swagger.apis.events.eventWebsocket(app=','.join(self.apps))
        # TypeChecker false positive on iter(callable, sentinel) -> iterator
        # Fixed in plugin v3.0.1
        # noinspection PyTypeChecker
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

    def on_channel_event(self, event_type, fn):
        event_model = self.event_models[event_type]
        if not event_model:
            raise ValueError("Cannot find event model '%s'" % event_type)

        channel_fields = [k for (k, v) in event_model.properties
                          if v.type == 'Channel']
        if not channel_fields:
            raise ValueError("Event model '%s' has not fields of type Channel"
                             % event_type)

        def fn_channels(event):
            channels = {channel_field: Channel(self, event[channel_field])
                        for channel_field in channel_fields
                        if event.get(channel_field)}
            # If there's only one channel field, just pass that along
            if len(channel_fields) == 1:
                if channels:
                    channels = channels.values()[0]
                else:
                    channels = None
            fn(channels, event)

        self.on_event(event_type, fn_channels)
