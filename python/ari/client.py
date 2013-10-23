#
# Copyright (c) 2013, Digium, Inc.
#

import json
import logging
import urlparse
import swaggerpy.client

from ari.model import *

log = logging.getLogger(__name__)


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
        self.global_listeners = []

        if isinstance(apps, str):
            apps = [apps]
        self.apps = apps or []

    def __getattr__(self, item):
        """Exposes repositories as Client fields.

        :param item: Field name
        """
        repo = self.repositories.get(item)
        if not repo:
            raise AttributeError(
                "AttributeError: '%r' object has no attribute '%s'" % (
                    self.__class__.__name__, item))
        return repo

    def run(self):
        """Connect to the WebSocket and begin processing messages.
        """
        ws = self.swagger.apis.events.eventWebsocket(app=','.join(self.apps))
        # TypeChecker false positive on iter(callable, sentinel) -> iterator
        # Fixed in plugin v3.0.1
        # noinspection PyTypeChecker
        for msg_str in iter(lambda: ws.recv(), None):
            msg_json = json.loads(msg_str)
            if not isinstance(msg_json, dict) or 'type' not in msg_json:
                log.error("Invalid event: %s" % msg_str)
                continue

            listeners = self.global_listeners + self.event_listeners.get(
                msg_json['type'], [])
            for listener in listeners:
                # noinspection PyBroadException
                try:
                    listener(msg_json)
                except Exception:
                    log.exception("Event listener threw exception")

    def on_event(self, event_type, event_cb):
        """Register callback for events with given type.

        :param event_type: String name of the event to register for.
        :param event_cb: Callback function
        :type  event_cb: (dict) -> None
        """
        listeners = self.event_listeners.get(event_type)
        if listeners is None:
            listeners = []
            self.event_listeners[event_type] = listeners
        listeners.append(event_cb)

    def on_object_event(self, event_type, event_cb, factory_fn, model_id):
        """Register callback for events with the given type. Event fields of
        the given model_id type are passed along to event_cb.

        If multiple fields of the event have the type model_id, a dict is
        passed mapping the field name to the model object.

        :param event_type: String name of the event to register for.
        :param event_cb: Callback function
        :type  event_cb: (Obj, dict) -> None or (dict[str, Obj], dict) ->
        :param factory_fn: Function for creating Obj from JSON
        :param model_id: String id for Obj from Swagger models.
        """
        event_model = self.event_models.get(event_type)
        if not event_model:
            raise ValueError("Cannot find event model '%s'" % event_type)

        obj_fields = [k for (k, v) in event_model['properties'].items()
                      if v['type'] == model_id]
        if not obj_fields:
            raise ValueError("Event model '%s' has no fields of type %s"
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
        """Register callback for Channel related events

        :param event_type: String name of the event to register for.
        :param fn: Callback function
        :type  fn: (Channel, dict) -> None or (list[Channel], dict) -> None
        """
        return self.on_object_event(event_type, fn, Channel, 'Channel')

    def on_bridge_event(self, event_type, fn):
        """Register callback for Bridge related events

        :param event_type: String name of the event to register for.
        :param fn: Callback function
        :type  fn: (Bridge, dict) -> None or (list[Bridge], dict) -> None
        """
        return self.on_object_event(event_type, fn, Bridge, 'Bridge')

    def on_playback_event(self, event_type, fn):
        """Register callback for Playback related events

        :param event_type: String name of the event to register for.
        :param fn: Callback function
        :type  fn: (Playback, dict) -> None or (list[Playback], dict) -> None
        """
        return self.on_object_event(event_type, fn, Playback, 'Playback')

    def on_endpoint_event(self, event_type, fn):
        """Register callback for Endpoint related events

        :param event_type: String name of the event to register for.
        :param fn: Callback function
        :type  fn: (Endpoint, dict) -> None or (list[Endpoint], dict) -> None
        """
        return self.on_object_event(event_type, fn, Endpoint, 'Endpoint')

    def on_sound_event(self, event_type, fn):
        """Register callback for Sound related events

        :param event_type: String name of the event to register for.
        :param fn: Sound function
        :type  fn: (Sound, dict) -> None or (list[Sound], dict) -> None
        """
        return self.on_object_event(event_type, fn, Sound, 'Sound')
