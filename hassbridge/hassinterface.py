"""hassbridge main module.

This implements the necessary parts of the homeassistant websocket API to communicate,
and create/control the dbus interfaces.
"""
import asyncio
import json
import logging
from pprint import pformat as pf
from urllib.parse import urlparse

import websockets
from dbus_next.aio import MessageBus

from .mprismain import MPrisInterface
from .playerinterface import PlayerInterface

_LOGGER = logging.getLogger(__name__)


class HassInterface:
    """Hass API interface, implements necessary parts of the websocket API."""

    def __init__(self, endpoint, token):
        self.ws = None
        self.http_endpoint = endpoint
        parsed = urlparse(self.http_endpoint)
        self.ws_endpoint = parsed._replace(scheme="ws", path="/api/websocket").geturl()

        self._token = token

        self._id = 0
        self._players = {}

        self._pending_requests = {}

    @property
    def _request_id(self) -> int:
        """Increment and return id for new request."""
        self._id += 1
        return self._id

    async def loop(self):
        """Listen to homeassistant websocket communication forever."""
        while True:
            msg = await self.ws.recv()
            response = await self.handle_message(msg)
            if response is not None:
                _LOGGER.debug("sending response: %s", response)
                await self.ws.send(response)

    async def execute_media_player_command(self, cmd, entity, params=None):
        """Execute the given media_player command on the given entity."""
        payload = {
            "type": "call_service",
            "domain": "media_player",
            "service": cmd,
            "service_data": {"entity_id": entity},
        }
        if params is not None:
            payload["service_data"].update(params)
        _LOGGER.debug("Going to execute %s on %s (payload: %s)", cmd, entity, payload)

        return await self._make_request(payload)

    def schedule_execution(self, target, *args, **kwargs):
        """Schedule execution of a coroutine from non-asyncio code.

        This is needed as some parts of the dbus_next api are not async.
        """
        loop = asyncio.get_event_loop()
        task = loop.create_task(target(*args, **kwargs))
        return task

    def schedule_seek(self, seek_to, entity):
        """Schedule execution of media seeking."""
        _LOGGER.debug("Requesting seek to %s on %s", seek_to, entity)
        self.schedule_execution(
            self.execute_media_player_command,
            "media_seek",
            entity,
            params={"seek_position": seek_to},
        )

    def schedule_set_volume(self, volume, entity):
        """Schedule volume setting."""
        _LOGGER.debug("Scheduling volume set to %s on %s", volume, entity)
        self.schedule_execution(
            self.execute_media_player_command,
            "volume_set",
            entity,
            params={"volume_level": volume},
        )

    async def update_player(self, entity, attrs):
        """Update (and create, if needed) the playback information.

        This gets called with the HASS API provided data during the
        initial state fetching, as well as for state change events.
        """
        if entity not in self._players:
            _LOGGER.info("Found new device, creating an interface for %s" % entity)
            self._players[entity] = await self.create_interface_for_entity(entity)

        _LOGGER.debug(
            "Updating data for hass player %s: state: %s", entity, attrs["state"]
        )
        self._players[entity].update_data(attrs)
        _LOGGER.debug("got new state: %s", pf(attrs))

    async def handle_event(self, msg):
        """Handle state changed event for media_players."""
        data = msg["event"]["data"]
        entity = data["entity_id"]
        if not entity.startswith("media_player."):
            return

        attrs = data["new_state"]
        await self.update_player(entity, attrs)

    async def handle_get_states_result(self, res):
        """Update states of currently playing devices."""
        for item in res:
            entity_id = item["entity_id"]
            if not entity_id.startswith("media_player."):
                continue

            state = item["state"]
            if state == "playing":
                _LOGGER.debug("%s is already playing, adding/updating..", entity_id)
                attrs = item["attributes"]
                attrs["entity_id"] = entity_id
                await self.update_player(entity_id, item)

    async def handle_call_service_result(self, res):
        """Handle call_service result."""
        pass

    async def handle_result(self, msg, request):
        """Dispatcher for API call results.

        This is responsible for error checking and executing the appropriate
        handlers based on the received message type.
        """
        if msg["success"] is False:
            _LOGGER.error("Call failed: %s" % msg["error"])
            return

        res = msg["result"]
        if res is None:
            _LOGGER.debug("missing result obj: %s, ignoring", msg)
            return

        request_type = request["type"]

        if request_type == "get_states":
            return await self.handle_get_states_result(res)
        elif request_type == "call_service":
            return await self.handle_call_service_result(res)
        else:
            _LOGGER.warning("unhandled request type: %s", request_type)

    async def handle_message(self, msg):
        """Parse incoming homeassistant messages."""
        msg = json.loads(msg)

        if msg["type"] == "event":
            return await self.handle_event(msg)
        elif msg["type"] == "result":
            request = self._pending_requests.pop(msg["id"], None)
            if request is None:
                _LOGGER.error("Got no request for %s", msg)
                return

            return await self.handle_result(msg, request)

    async def _make_request(self, data):
        """Wrap the data to expected format and send it to to the ws endpoint."""
        _id = self._request_id
        data = {**data, "id": _id}

        self._pending_requests[_id] = data
        req = json.dumps(data)

        return await self.ws.send(req)

    async def subscribe(self):
        """Subscribe to state_changed events."""
        payload = {"type": "subscribe_events", "event_type": "state_changed"}
        _LOGGER.debug("Going to subscribe to state_changed events..")
        return await self._make_request(payload)

    async def find_players(self):
        """Request all current states to find already active media players."""
        list_players_payload = {"type": "get_states"}
        _LOGGER.debug("Trying to find already existing, playing players..")
        await self._make_request(list_players_payload)

    async def handle_auth(self):
        """Handle authentication to hass ws api."""
        req = await self.ws.recv()
        res_json = json.loads(req)

        if "type" in res_json:
            if res_json["type"] == "auth_required":
                await self.ws.send(
                    json.dumps({"type": "auth", "access_token": self._token})
                )
                auth_response = json.loads(await self.ws.recv())
                if auth_response["type"] == "auth_ok":
                    _LOGGER.info(
                        "Successfully authed to %s, running %s",
                        self.ws_endpoint,
                        auth_response["ha_version"],
                    )
                else:
                    # auth_invalid
                    raise Exception(
                        "Unknown response/invalid token: %s" % auth_response
                    )

    async def start(self):
        """Connect to homeassistant and start the communication loop."""
        _LOGGER.info("Connecting to %s", self.ws_endpoint)

        try:
            async with websockets.connect(self.ws_endpoint) as ws:
                self.ws = ws
                _LOGGER.info("Got connected, doing auth..")
                await self.handle_auth()

                _LOGGER.info("Auth success, subscribing for events")
                await self.subscribe()

                _LOGGER.info("Finding already playing players")
                await self.find_players()

                _LOGGER.info("Starting main loop")
                await self.loop()
        except Exception as ex:
            _LOGGER.error("Got error during communication: %s", ex, exc_info=False)
            await asyncio.sleep(5)
            await self.start()

    async def create_interface_for_entity(self, player_entity) -> PlayerInterface:
        """Create mpris interfaces for given homeassistant player."""
        bus = await MessageBus().connect()

        interface = MPrisInterface("org.mpris.MediaPlayer2", self)
        player_interface = PlayerInterface("org.mpris.MediaPlayer2.Player", self)

        bus.export("/org/mpris/MediaPlayer2", interface)
        bus.export("/org/mpris/MediaPlayer2", player_interface)

        # register ourselves using the entity id
        await bus.request_name(f"org.mpris.MediaPlayer2.hassbridge.{player_entity}")

        return player_interface
