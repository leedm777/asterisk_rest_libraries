#!/usr/bin/env python

import re
import requests
import logging

log = logging.getLogger(__name__)


def promote(client, resp, operation_json):
    resp.raise_for_status()

    response_class = operation_json['responseClass']
    is_list = False
    m = re.match('''List\[(.*)\]''', response_class)
    if m:
        response_class = m.group(1)
        is_list = True
    factory = CLASS_MAP.get(response_class)
    if factory:
        resp_json = resp.json()
        if is_list:
            return [factory(client, obj) for obj in resp_json]
        return factory(client, resp_json)
    if resp.status_code == requests.codes.no_content:
        return None
    log.info("No first class model for %s; returning JSON" % response_class)
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
        if not (hasattr(oper, '__call__') and hasattr(oper, 'json')):
            raise AttributeError(
                "'%s' object has no attribute '%r'" % (
                    self.__class__.__name__, item))

        return lambda **kwargs: promote(self.client, oper(**kwargs), oper.json)


class BaseObject(object):
    def __init__(self, client, api, as_json, param_name, factory_fn, model_id):
        self.client = client
        self.api = api
        self.json = as_json
        self.id = as_json['id']
        self.param_name = param_name
        self.model_id = model_id
        self.factory_fn = factory_fn

    def __repr__(self):
        return "Repository(%s)" % self.name

    def __getattr__(self, item):
        oper = getattr(self.api, item)
        if not (hasattr(oper, '__call__') and hasattr(oper, 'json')):
            raise AttributeError(
                "'%s' object has no attribute '%r'" % (
                    self.__class__.__name__, item))

        def promoter(**kwargs):
            # Add id to param list
            kwargs[self.param_name] = self.id
            return promote(self.client, oper(**kwargs), oper.json)

        return promoter

    def on_event(self, event_type, fn):
        def fn_filter(objects, event):
            if isinstance(objects, dict):
                if self.id in [c.id for c in objects.values()]:
                    fn(objects, event)
            else:
                if self.id == objects.id:
                    fn(objects, event)

        self.client.on_object_event(event_type, fn_filter, self.factory_fn,
                                    self.model_id)


class Channel(BaseObject):
    def __init__(self, client, channel_json):
        super(Channel, self).__init__(
            client, client.swagger.apis.channels, channel_json, 'channelId',
            Channel, 'Channel')


class Bridge(BaseObject):
    def __init__(self, client, bridge_json):
        super(Bridge, self).__init__(
            client, client.swagger.apis.bridges, bridge_json, 'bridgeId',
            Bridge, 'Bridge')


class Playback(BaseObject):
    def __init__(self, client, playback_json):
        super(Playback, self).__init__(
            client, client.swagger.apis.playback, playback_json, 'playbackId',
            Playback, 'Playback')


CLASS_MAP = {
    'Channel': Channel,
    'Bridge': Bridge,
    'Playback': Playback
}
