import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set

from db import async_session_scope
from db.plaato_data import PlaatoData as PlaatoDataDB
from lib import logging
from lib.config import Config
from lib.devices.plaato_keg import blynk_protocol, plaato_data, plaato_protocol
from lib.devices.plaato_keg.command_writer import Commands
from lib.devices.plaato_keg.data_processor import DataProcessor

LOGGER = logging.getLogger(__name__)
CONFIG = Config()


@dataclass
class ConnectionState:
    """State for a single keg connection"""

    device_id: Optional[str] = None
    processor: Optional[DataProcessor] = None
    reader: Optional[asyncio.StreamReader] = None
    writer: Optional[asyncio.StreamWriter] = None


class ConnectionHandler:
    """Handles TCP connections from Plaato Keg devices"""

    def __init__(self):
        self.connections: Dict[str, ConnectionState] = {}
        self.socket_registry: Dict[str, ConnectionState] = {}
        self._running = False
        self._server: Optional[asyncio.Server] = None

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new device connection"""
        addr = writer.get_extra_info("peername")
        LOGGER.info(f"New connection from {addr}")

        processor = DataProcessor()
        state = ConnectionState(processor=processor, reader=reader, writer=writer)

        connection_id = f"{addr[0]}:{addr[1]}"
        self.connections[connection_id] = state

        try:
            while True:
                LOGGER.debug("Reading data...")
                data = await asyncio.wait_for(reader.read(1024), timeout=300)
                LOGGER.debug(f"data read: {data}")

                if not data:
                    LOGGER.debug("no data, bailing and closing the connection")
                    break

                writer.write(blynk_protocol.response_success())
                await writer.drain()

                await processor.process_data(data)

                if self._register_new_socket(data, state):
                    await self._send_user_override_commands(state.device_id)

        except asyncio.TimeoutError:
            LOGGER.warning(f"Connection timed out: {addr}")
        except asyncio.CancelledError:
            LOGGER.info(f"Connection cancelled: {addr}")
        except Exception as e:
            LOGGER.error(f"Error handling connection from {addr}.  {e}", stack_info=True, exc_info=True)
        finally:
            await self._cleanup_connection(connection_id, state)

    async def _send_user_override_commands(self, device_id):

        commands = []
        async with async_session_scope(CONFIG) as db_session:
            dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
            if dev:
                if dev.user_keg_mode_c02_beer:
                    commands.append((Commands.SET_MODE, dev.user_keg_mode_c02_beer))
                if dev.user_unit:
                    commands.append((Commands.SET_UNIT, dev.user_unit))
                if dev.user_measure_unit:
                    commands.append((Commands.SET_MEASURE_UNIT, dev.user_measure_unit))

        if commands:
            from lib.devices.plaato_keg import service_handler

            command_writer = service_handler.command_writer
            LOGGER.info(f"Sending user overrideable commands to keg {device_id}: {commands}")
            for cmd, val in commands:
                await command_writer.send_command(device_id, cmd, val)

    async def _cleanup_connection(self, connection_id: str, state: ConnectionState):
        """Clean up a closed connection"""
        LOGGER.debug(f"Attempting to clean up connection id: {connection_id}")

        if state.device_id and state.device_id in self.socket_registry:
            found = False
            for conn_id, conn_state in self.connections.items():
                if conn_id == connection_id:
                    continue
                if conn_state.device_id and state.device_id == conn_state.device_id:
                    found = True
                    break
            if not found:
                LOGGER.info(f"Keg {state.device_id} disconnected")
                del self.socket_registry[state.device_id]

        if connection_id in self.connections:
            del self.connections[connection_id]

        if state.writer:
            state.writer.close()
            await state.writer.wait_closed()

    def _register_new_socket(self, data: bytes, state: ConnectionState) -> bool:
        """Register socket if keg ID is found in data"""
        LOGGER.debug(f"Attempting to register new device connection...")
        if state.device_id:
            LOGGER.debug(f"Connection already registered, device_id: {state.device_id}")
            return False

        device_id = state.device_id
        if not device_id:
            LOGGER.debug(f"extracting keg id....")
            device_id = self._extract_device_id(data)

        if device_id:
            LOGGER.info(f"Registering socket for keg {device_id}")
            state.device_id = device_id
            self.socket_registry[device_id] = state
            return True

        return False

    def _extract_device_id(self, data: bytes) -> Optional[str]:
        """Extract keg ID from incoming data"""
        try:
            messages = blynk_protocol.decode(data)
            processed = plaato_protocol.decode_list(messages)
            decoded = plaato_data.decode_list(processed)

            for key, value, _ in decoded:
                if key == "id":
                    if isinstance(value, bytes):
                        return value.decode("utf-8")
                    return str(value)

            return None
        except Exception as e:
            LOGGER.error(f"Error extracting keg ID: {e}", stack_info=True, exc_info=True)
            return None

    async def send_command_to_keg(self, device_id: str, command: bytes) -> bool:
        """Send a command to a specific keg"""
        if device_id not in self.socket_registry:
            LOGGER.warning(f"No connection found for keg {device_id}")
            return False

        state = self.socket_registry[device_id]
        if not state.writer:
            LOGGER.warning(f"No writer available for keg {device_id}")
            return False

        try:
            state.writer.write(command)
            await state.writer.drain()
            return True
        except Exception as e:
            LOGGER.error(f"Error sending command to keg {device_id}", stack_info=True, exc_info=True)
            return False

    def get_registered_device_ids(self) -> Set[str]:
        """Get list of currently connected keg IDs"""
        return set(self.socket_registry.keys())

    def get_connection_ids(self) -> Set[str]:
        """Get list of currently connected keg IDs"""
        return set(self.connections.keys())

    async def start_server(self, host: str, port: int):
        """Start the TCP server"""
        LOGGER.info(f"Starting TCP server on {host}:{port}")
        self._running = True

        self._server = await asyncio.start_server(self.handle_connection, host, port)

        async with self._server:
            await self._server.serve_forever()

    async def stop_server(self):
        """Stop the TCP server"""
        LOGGER.info("Stopping TCP server")
        self._running = False

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for connection_id, state in list(self.connections.items()):
            await self._cleanup_connection(connection_id, state)
