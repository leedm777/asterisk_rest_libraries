#!/usr/bin/env python

import re


def promote(resp, response_class):
    resp.raise_for_status()

    clazz = response_class
    is_list = False
    m = re.match('''List\[(.*)\]''', clazz)
    if m:
        clazz = m.group(1)
        is_list = True
    factory = CLASS_MAP.get(clazz)
    if factory:
        resp_json = resp.json()
        if is_list:
            return [factory(obj) for obj in resp_json]
        return factory(resp_json)
    return resp.json()


class Repository(object):
    def __init__(self, client, name, api):
        self.client = client
        self.name = name
        self.api = api

    def __repr__(self):
        return "Repository(%s)" % self.name

    def __getattr__(self, item):
        oper = getattr(self.api, item)
        if not (hasattr(oper, '__call__') and hasattr(oper, 'response_class')):
            raise AttributeError(
                "'%s' object has no attribute '%r'" % (
                    self.__class__.__name__, item))

        return lambda **kwargs: promote(oper(**kwargs), oper.response_class)


class DomainObject(object):
    def __init__(self, client, api, as_json, param_name):
        self.client = client
        self.api = api
        self.json = as_json
        self.id = as_json['id']
        self.param_name = param_name

    def __repr__(self):
        return "Repository(%s)" % self.name

    def __getattr__(self, item):
        oper = getattr(self.api, item)
        if not (hasattr(oper, '__call__') and hasattr(oper, 'response_class')):
            raise AttributeError(
                "'%s' object has no attribute '%r'" % (
                    self.__class__.__name__, item))

        def promoter(**kwargs):
            # Add id to param list
            kwargs[self.param_name] = self.id
            promote(oper(**kwargs), oper.response_class)

        return promoter


class Channel(DomainObject):
    def __init__(self, client, channel_json):
        super(Channel, self).__init__(client, client.swagger.apis.channels,
                                      channel_json, 'channelId')

    def on_event(self, event_type, fn):
        def fn_filter(channels, event):
            if isinstance(channels, dict):
                if self.id in [c.id for c in channels.values()]:
                    fn(channels, event)
            else:
                if self.id == channels.id:
                    fn(channels, event)

        self.client.on_channel_event(event_type, fn_filter)


class Bridge(DomainObject):
    def __init__(self, client, bridge_json):
        super(Bridge, self).__init__(client, client.swagger.apis.bridges,
                                     bridge_json, 'bridgeId')

    def on_event(self, event_type, fn):
        def fn_filter(bridges, event):
            if isinstance(bridges, dict):
                if self.id in [c.id for c in bridges.values()]:
                    fn(bridges, event)
            else:
                if self.id == bridges.id:
                    fn(bridges, event)

        self.client.on_bridge_event(event_type, fn_filter)


CLASS_MAP = {
    'Channel': Channel,
    'Bridge': Bridge
}
