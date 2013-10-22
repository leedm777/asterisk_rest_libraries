#
# Copyright (c) 2013, Digium, Inc.
#

import json
import logging
import urlparse
import requests
import requests.auth
import swaggerpy.client
from model import Channel, Bridge, Repository

log = logging.getLogger(__name__)


class AriBasicAuthFactory(object):
    """ARI session factory, using HTTP Basic auth

    :param username: ARI username
    :param password: ARI password
    """

    def __init__(self, username, password):
        self.auth = requests.auth.HTTPBasicAuth(username, password)

    def build_session(self):
        """Build a session for use with ARI.
        """
        session = requests.Session()
        session.auth = self.auth
        return session


class Client(object):
    """ARI Client object.

    :param base_url: Base URL for accessing Asterisk.
    :param http_client: HTTP client interface.
    :param apps:
    """

    def __init__(self, base_url, http_client, apps=None):
        url = urlparse.urljoin(base_url, "ari/api-docs/resources.json")

        self.swagger = swaggerpy.client.SwaggerClient(
            url, http_client=http_client)
        self.repositories = {
            name: Repository(self, name, api)
            for (name, api) in self.swagger.apis.resources.items()}

        events = [api['api_declaration']
                  for api in self.swagger.api_docs['apis']
                  if api['name'] == 'events']
        if events:
            self.event_models = events[0]['models']
        else:
            self.event_models = {}

        self.event_listeners = {}

        if isinstance(apps, str):
            apps = [apps]
        self.apps = apps or []

    def __getattr__(self, item):
        return self.repositories[item]

    def run(self):
        ws = self.swagger.apis.events.eventWebsocket(app=','.join(self.apps))
        # TypeChecker false positive on iter(callable, sentinel) -> iterator
        # Fixed in plugin v3.0.1
        # noinspection PyTypeChecker
        for msg_str in iter(lambda: ws.recv(), None):
            msg_json = json.loads(msg_str)
            for listener in self.event_listeners.get(
                    msg_json.get('type')) or []:
                # noinspection PyBroadException
                try:
                    listener(msg_json)
                except Exception:
                    log.exception("Event listener threw exception")

    def on_event(self, event_type, fn):
        listeners = self.event_listeners.get(event_type)
        if listeners is None:
            listeners = []
            self.event_listeners[event_type] = listeners
        listeners.append(fn)

    def on_object_event(self, event_type, event_cb, factory_fn, model_id):
        event_model = self.event_models[event_type]
        if not event_model:
            raise ValueError("Cannot find event model '%s'" % event_type)

        obj_fields = [k for (k, v) in event_model['properties'].items()
                      if v['type'] == model_id]
        if not obj_fields:
            raise ValueError("Event model '%s' has not fields of type %s"
                             % (event_type, model_id))

        def fn_channels(event):
            obj = {obj_field: factory_fn(self, event[obj_field])
                   for obj_field in obj_fields
                   if event.get(obj_field)}
            # If there's only one channel field, just pass that along
            if len(obj_fields) == 1:
                if obj:
                    obj = obj.values()[0]
                else:
                    obj = None
            event_cb(obj, event)

        self.on_event(event_type, fn_channels)

    def on_channel_event(self, event_type, fn):
        return self.on_object_event(event_type, fn, Channel, 'Channel')

    def on_bridge_event(self, event_type, fn):
        return self.on_object_event(event_type, fn, Bridge, 'Bridge')
