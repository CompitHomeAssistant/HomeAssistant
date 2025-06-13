import asyncio
from typing import Any, List
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers import event as ha_event
import logging
from datetime import datetime, timedelta
import json

from .types.SystemInfo import Gate
from .types.DeviceDefinitions import DeviceDefinitions
from .types.DeviceState import DeviceInstance
from .api import CompitFullAPI
from .const import DOMAIN

SCAN_INTERVAL = timedelta(minutes=1)
_LOGGER: logging.Logger = logging.getLogger(__package__)


class CompitDataUpdateCoordinatorPush(DataUpdateCoordinator[dict[Any, DeviceInstance]]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        gates: List[Gate],
        api: CompitFullAPI,
        device_definitions: DeviceDefinitions,
    ) -> None:
        """Initialize."""
        self.devices: dict[Any, DeviceInstance] = {}
        self.api = api
        self.platforms = []
        self.gates = gates
        self.device_definitions = device_definitions
        self.hass = hass
        self.websocket = None
        self._websocket_task = None
        self._heartbeat_task = None
        self._heartbeat_no = 8
        self._vent_group_requested: None | datetime = None
        self.vent_group_id = None

        super().__init__(hass, _LOGGER, name=DOMAIN)

    async def _async_update_data(self):
        """No periodic polling, data is pushed via websocket."""
        # This method is required by DataUpdateCoordinator but we won't use it for polling
        # as updates come via the websocket.
        return {}

    async def _start_websocket(self):
        """Start the websocket connection and listener."""
        # while True:
        try:
            _LOGGER.info("Connecting to websocket...")
            self.websocket = await self.api.connect_websocket()
            _LOGGER.info("Websocket connected.")
            # Send initial packets
            await self.websocket.send_str(
                json.dumps(["4", "4", f"gates:{self.gates[0].id}", "phx_join", {}])
            )
            await self.websocket.send_str(
                json.dumps(
                    ["7", "7", f"devices:{self.gates[0].devices[0].id}", "phx_join", {}]
                )
            )

            self.vent_group_id = await self.api.get_wentilation_group_id(
                gate_id=self.gates[0].id,
                device_class=self.gates[0].devices[0].class_,
                device_type=self.gates[0].devices[0].type,
                device_version=self.gates[0].devices[0].version,
            )
            # Listen for messages
            self._websocket_task = self.hass.async_create_background_task(
                self._listen_for_messages(),
                "websocket_listener",
            )

            # Register periodic tasks
            self._heartbeat_task = ha_event.async_track_time_interval(
                self.hass,
                self._send_heartbeat,
                timedelta(seconds=30),
            )
            # Request more params
            self._requester_task = ha_event.async_track_time_interval(
                self.hass,
                self._request_parameters,
                timedelta(seconds=30),
            )

        except Exception as e:
            _LOGGER.error("Websocket error: %s", e, exc_info=True)
            self.websocket = None

    async def _listen_for_messages(self):
        """Listen for incoming messages from the websocket."""
        while self.websocket:
            try:
                message = await self.websocket.receive()
                if message.type == aiohttp.WSMsgType.TEXT:
                    _LOGGER.info("Received message: %s", message.data[:16])
                    self._handle_websocket_message(json.loads(message.data))
                elif message.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.warning(
                        "Websocket connection closed: %s", self.websocket.exception()
                    )

            except Exception as e:
                _LOGGER.error(
                    "Error receiving or processing websocket: %s",
                    e,
                    exc_info=True,
                )

            await asyncio.sleep(0.1)

        _LOGGER.error("Websocket disconnected. Reconnecting in 5 seconds...")
        self.stop_websocket()
        asyncio.sleep(5)
        self.hass.async_create_task(self._start_websocket())

    @callback
    def _handle_websocket_message(self, message: list):
        """Handle an incoming websocket message and update Home Assistant entities."""
        _LOGGER.debug("Handling message: %s", str(message)[:64])

        if message[3] in ["state_update", "selected_params_update"]:
            update_data = message[4]

            if message[3] == "selected_params_update":
                self._vent_group_requested = None

            for gate in self.gates:
                if gate.id != update_data.get("gate_id"):
                    continue
                for device in gate.devices:
                    if device.id != update_data.get("device_id"):
                        continue

                    if device.id not in self.devices:
                        self.devices[device.id] = DeviceInstance(
                            next(
                                filter(
                                    lambda item: item._class == device.class_
                                    and item.code == device.type,
                                    self.device_definitions.devices,
                                ),
                                None,
                            )
                        )
                        state = self.api.get_state(gate_id=gate.id, device_id=device.id)
                        self.devices[device.id].state = state
                    elif self.devices[device.id].state:
                        self.devices[device.id].state.update_from_json(
                            update_data.get("state")
                        )
                        self.devices[
                            device.id
                        ].state.last_connected_at = datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                    self.async_set_updated_data(self.devices)

    async def _send_heartbeat(self, now):
        """Send a heartbeat message every 30 seconds."""
        if self.websocket:
            try:
                heartbeat_packet = [
                    None,
                    f"{self._heartbeat_no}",
                    "phoenix",
                    "heartbeat",
                    {},
                ]
                self._heartbeat_no += 1
                _LOGGER.info("Sending heartbeat packet: %s", heartbeat_packet)
                await self.websocket.send_str(json.dumps(heartbeat_packet))
            except Exception as e:
                _LOGGER.error("Error sending heartbeat: %s", e)

    async def _request_parameters(self, now):
        if self.websocket:
            try:
                if (
                    not self._vent_group_requested
                    or datetime.now() - self._vent_group_requested
                    > timedelta(minutes=5)
                ):
                    _LOGGER.info(
                        f"Requesting parameters for group {self.vent_group_id}..."
                    )
                    await self.api.request_parameters(
                        self.gates[0].code,
                        self.gates[0].devices[0].id,
                        self.vent_group_id,
                    )
                    self._vent_group_requested = datetime.now()
            except Exception as e:
                _LOGGER.error("Error requesting parameters: %s", e)

    async def async_config_entry_first_refresh(self):
        """Start the websocket connection when the integration is loaded."""

        try:
            for gate in self.gates:
                for device in gate.devices:
                    if device.id not in self.devices:
                        self.devices[device.id] = DeviceInstance(
                            next(
                                filter(
                                    lambda item: item._class == device.class_
                                    and item.code == device.type,
                                    self.device_definitions.devices,
                                ),
                                None,
                            )
                        )
                    state = await self.api.get_state(
                        gate_id=gate.id, device_id=device.id
                    )
                    self.devices[device.id].state = state
                    self.async_set_updated_data(self.devices)

        except Exception as exception:
            raise UpdateFailed() from exception

        await self._start_websocket()

    async def stop_websocket(self):
        """Stop the websocket connection and associated tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            await self._heartbeat_task
        if self._websocket_task:
            self._websocket_task.cancel()
            await self._websocket_task
        if self._requester_task:
            self._requester_task.cancel()
            await self._requester_task
        if self.websocket:
            await self.websocket.close()
        _LOGGER.info("Websocket connection stopped.")
