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


class ObjectIdentifier(object):
    def get_params(self, obj_json):
        raise NotImplementedError("Not implemented")

    def id_as_str(self, obj_json):
        raise NotImplementedError("Not implemented")


class DefaultObjectIdentifier(ObjectIdentifier):
    def __init__(self, param_name, id_field='id'):
        self.param_name = param_name
        self.id_field = id_field

    def get_params(self, obj_json):
        return {self.param_name: obj_json[self.id_field]}

    def id_as_str(self, obj_json):
        return obj_json[self.id_field]


class BaseObject(object):
    def __init__(self, client, api, as_json, identifier, event_reg):
        self.client = client
        self.api = api
        self.json = as_json
        self.event_reg = event_reg
        self.identifier = identifier
        self.id = identifier.id_as_str(as_json)

    def __repr__(self):
        return "%s(%s)=%r" % (self.__class__.__name__, self.id, self.json)

    def __getattr__(self, item):
        oper = getattr(self.api, item)
        if not (hasattr(oper, '__call__') and hasattr(oper, 'json')):
            raise AttributeError(
                "'%s' object has no attribute '%r'" % (
                    self.__class__.__name__, item))

        def promoter(**kwargs):
            # Add id to param list
            kwargs.update(self.identifier.get_params(self.json))
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
            client, client.swagger.apis.channels, channel_json,
            DefaultObjectIdentifier('channelId'), client.on_channel_event)


class Bridge(BaseObject):
    def __init__(self, client, bridge_json):
        super(Bridge, self).__init__(
            client, client.swagger.apis.bridges, bridge_json,
            DefaultObjectIdentifier('bridgeId'), client.on_bridge_event)


class Playback(BaseObject):
    def __init__(self, client, playback_json):
        super(Playback, self).__init__(
            client, client.swagger.apis.playback, playback_json,
            DefaultObjectIdentifier('playbackId'), client.on_playback_event)


class EndpointIdentifier(ObjectIdentifier):
    def get_params(self, obj_json):
        return {
            'tech': obj_json['technology'],
            'resource': obj_json['resource']
        }

    def id_as_str(self, obj_json):
        return "%(tech)s/%(resource)s" % self.get_params(obj_json)


class Endpoint(BaseObject):
    def __init__(self, client, endpoint_json):
        super(Endpoint, self).__init__(
            client, client.swagger.apis.endpoints, endpoint_json,
            EndpointIdentifier(), client.on_endpoint_event)


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
