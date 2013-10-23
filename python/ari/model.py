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
    def __init__(self, client, api, as_json, param_name, event_reg,
                 get_id=lambda json: json['id']):
        self.client = client
        self.api = api
        self.json = as_json
        self.id = get_id(as_json)
        self.param_name = param_name
        self.event_reg = event_reg

    def __repr__(self):
        return "%s(%s) {%r}" % (self.__class__.__name__, self.id, self.json)

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

        self.event_reg(event_type, fn_filter)


class Channel(BaseObject):
    def __init__(self, client, channel_json):
        super(Channel, self).__init__(
            client, client.swagger.apis.channels, channel_json, 'channelId',
            client.on_channel_event)


class Bridge(BaseObject):
    def __init__(self, client, bridge_json):
        super(Bridge, self).__init__(
            client, client.swagger.apis.bridges, bridge_json, 'bridgeId',
            client.on_bridge_event)


class Playback(BaseObject):
    def __init__(self, client, playback_json):
        super(Playback, self).__init__(
            client, client.swagger.apis.playback, playback_json, 'playbackId',
            client.on_playback_event)


def endpoint_get_id(json):
    return "%s/%s" % (json['technology'], json['resource'])


class Endpoint(BaseObject):
    def __init__(self, client, endpoint_json):
        super(Endpoint, self).__init__(
            client, client.swagger.apis.endpoints, endpoint_json, 'endpointId',
            client.on_endpoint_event, get_id=endpoint_get_id)


class Sound(BaseObject):
    def __init__(self, client, sound_json):
        super(Sound, self).__init__(
            client, client.swagger.apis.sounds, sound_json, 'soundId',
            client.on_sound_event)


CLASS_MAP = {
    'Bridge': Bridge,
    'Channel': Channel,
    'Endpoint': Endpoint,
    'Playback': Playback
}
