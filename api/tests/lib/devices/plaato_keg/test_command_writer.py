"""Tests for command_writer module"""

import struct
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from lib.devices.plaato_keg.blynk_protocol import BlynkCommand
from lib.devices.plaato_keg.plaato_protocol import PlaatoPin
from lib.devices.plaato_keg.command_writer import (
    Commands,
    COMMAND_MAPP,
    sanitize_command,
    command_from_pin,
    CommandWriter,
)

# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestCommands:
    """Tests for Commands enum"""

    def test_command_values(self):
        """Test that command values are correct"""
        assert Commands.SET_MODE == "set-mode"
        assert Commands.SET_UNIT == "set-unit"
        assert Commands.SET_MEASURE_UNIT == "set-measure-unit"
        assert Commands.SET_EMPTY_KEG_WEIGHT == "set-empty-keg-weight"
        assert Commands.SET_MAX_KEG_VOLUME == "set-max-keg-volume"


class TestCommandMapp:
    """Tests for COMMAND_MAPP"""

    def test_set_mode_mapping(self):
        """Test SET_MODE is mapped correctly"""
        assert Commands.SET_MODE in COMMAND_MAPP
        assert COMMAND_MAPP[Commands.SET_MODE]["pin"] == PlaatoPin.MODE

    def test_set_unit_mapping(self):
        """Test SET_UNIT is mapped correctly"""
        assert Commands.SET_UNIT in COMMAND_MAPP
        assert COMMAND_MAPP[Commands.SET_UNIT]["pin"] == PlaatoPin.UNIT

    def test_set_measure_unit_mapping(self):
        """Test SET_MEASURE_UNIT is mapped correctly"""
        assert Commands.SET_MEASURE_UNIT in COMMAND_MAPP
        assert COMMAND_MAPP[Commands.SET_MEASURE_UNIT]["pin"] == PlaatoPin.MEASURE_UNIT

    def test_set_empty_keg_weight_mapping(self):
        """Test SET_EMPTY_KEG_WEIGHT is mapped correctly"""
        assert Commands.SET_EMPTY_KEG_WEIGHT in COMMAND_MAPP
        assert COMMAND_MAPP[Commands.SET_EMPTY_KEG_WEIGHT]["pin"] == PlaatoPin.EMPTY_KEG_WEIGHT

    def test_set_max_keg_volume_mapping(self):
        """Test SET_MAX_KEG_VOLUME is mapped correctly"""
        assert Commands.SET_MAX_KEG_VOLUME in COMMAND_MAPP
        assert COMMAND_MAPP[Commands.SET_MAX_KEG_VOLUME]["pin"] == PlaatoPin.MAX_KEG_VOLUME


class TestSanitizeCommand:
    """Tests for sanitize_command function"""

    def test_lowercase(self):
        """Test command is lowercased"""
        result = sanitize_command("SET_MODE")
        assert result == "set-mode"

    def test_underscore_to_dash(self):
        """Test underscores are replaced with dashes"""
        result = sanitize_command("set_empty_keg_weight")
        assert result == "set-empty-keg-weight"

    def test_already_correct_format(self):
        """Test command already in correct format"""
        result = sanitize_command("set-mode")
        assert result == "set-mode"

    def test_mixed_case_and_underscores(self):
        """Test mixed case with underscores"""
        result = sanitize_command("Set_Measure_Unit")
        assert result == "set-measure-unit"


class TestCommandFromPin:
    """Tests for command_from_pin function"""

    def test_mode_pin(self):
        """Test getting command from MODE pin"""
        result = command_from_pin(PlaatoPin.MODE)
        assert result == Commands.SET_MODE

    def test_unit_pin(self):
        """Test getting command from UNIT pin"""
        result = command_from_pin(PlaatoPin.UNIT)
        assert result == Commands.SET_UNIT

    def test_measure_unit_pin(self):
        """Test getting command from MEASURE_UNIT pin"""
        result = command_from_pin(PlaatoPin.MEASURE_UNIT)
        assert result == Commands.SET_MEASURE_UNIT

    def test_string_pin(self):
        """Test getting command from pin as string"""
        result = command_from_pin(str(PlaatoPin.MODE))
        assert result == Commands.SET_MODE

    def test_unknown_pin(self):
        """Test unknown pin returns None"""
        result = command_from_pin(999)
        assert result is None

    def test_empty_keg_weight_pin(self):
        """Test getting command from EMPTY_KEG_WEIGHT pin"""
        result = command_from_pin(PlaatoPin.EMPTY_KEG_WEIGHT)
        assert result == Commands.SET_EMPTY_KEG_WEIGHT


class TestCommandWriter:
    """Tests for CommandWriter class"""

    @pytest.fixture
    def mock_connection_handler(self):
        """Create a mock connection handler"""
        handler = MagicMock()
        handler.send_command_to_keg = AsyncMock(return_value=True)
        handler.get_connected_kegs = MagicMock(return_value=["keg1", "keg2"])
        return handler

    @pytest.fixture
    def command_writer(self, mock_connection_handler):
        """Create a CommandWriter with mock handler"""
        return CommandWriter(mock_connection_handler)

    def test_init(self, command_writer, mock_connection_handler):
        """Test CommandWriter initialization"""
        assert command_writer.connection_handler == mock_connection_handler
        assert command_writer.msg_id_counter == 1

    def test_get_next_msg_id(self, command_writer):
        """Test message ID counter increments"""
        assert command_writer._get_next_msg_id() == 1
        assert command_writer._get_next_msg_id() == 2
        assert command_writer._get_next_msg_id() == 3

    def test_get_next_msg_id_wraps(self, command_writer):
        """Test message ID counter wraps at 65535"""
        command_writer.msg_id_counter = 65535
        assert command_writer._get_next_msg_id() == 65535
        assert command_writer._get_next_msg_id() == 1  # Wraps

    def test_get_connected_kegs(self, command_writer):
        """Test getting connected kegs"""
        kegs = command_writer.get_connected_kegs()
        assert kegs == ["keg1", "keg2"]

    def test_send_hardware_command(self, command_writer, mock_connection_handler):
        """Test sending hardware command"""
        result = run_async(command_writer._send_hardware_command("device123", PlaatoPin.MODE, "01"))

        assert result is True
        mock_connection_handler.send_command_to_keg.assert_called_once()

        # Verify the command was encoded correctly
        call_args = mock_connection_handler.send_command_to_keg.call_args
        device_id = call_args[0][0]
        command_bytes = call_args[0][1]

        assert device_id == "device123"

        # Verify it's a valid Blynk HARDWARE command
        cmd, msg_id, length = struct.unpack('>BHH', command_bytes[:5])
        assert cmd == BlynkCommand.HARDWARE

    def test_send_command_set_mode(self, command_writer, mock_connection_handler):
        """Test sending SET_MODE command"""
        result = run_async(command_writer.send_command("device123", Commands.SET_MODE, "1"))

        assert result is True
        mock_connection_handler.send_command_to_keg.assert_called_once()

    def test_send_command_sanitizes(self, command_writer, mock_connection_handler):
        """Test that send_command sanitizes command name"""
        result = run_async(command_writer.send_command("device123", "SET_MODE", "1"))

        assert result is True
        mock_connection_handler.send_command_to_keg.assert_called_once()

    def test_send_command_unknown_returns_false(self, command_writer):
        """Test sending unknown command returns False"""
        result = run_async(command_writer.send_command("device123", "unknown-command", "value"))

        assert result is False

    def test_send_command_no_value_returns_false(self, command_writer):
        """Test sending command without value returns False"""
        result = run_async(command_writer.send_command("device123", Commands.SET_MODE, None))

        assert result is False

    def test_send_command_empty_value_returns_false(self, command_writer):
        """Test sending command with empty value returns False"""
        result = run_async(command_writer.send_command("device123", Commands.SET_MODE, ""))

        assert result is False

    def test_send_hardware_command_failure(self, command_writer, mock_connection_handler):
        """Test handling send failure"""
        mock_connection_handler.send_command_to_keg = AsyncMock(return_value=False)

        result = run_async(command_writer._send_hardware_command("device123", PlaatoPin.MODE, "01"))

        assert result is False

    def test_send_command_with_static_value(self, command_writer, mock_connection_handler):
        """Test command with static value in COMMAND_MAPP would use that value"""
        # For now, none of the commands have static values enabled
        # This test verifies the logic path exists
        result = run_async(command_writer.send_command("device123", Commands.SET_EMPTY_KEG_WEIGHT, "5.0"))

        assert result is True

    def test_send_command_value_converted_to_string(self, command_writer, mock_connection_handler):
        """Test that numeric values are converted to strings"""
        result = run_async(command_writer.send_command("device123", Commands.SET_EMPTY_KEG_WEIGHT, 5.0))

        assert result is True

        # Verify the command was sent
        call_args = mock_connection_handler.send_command_to_keg.call_args
        command_bytes = call_args[0][1]

        # The body should contain the string "5.0"
        assert b"5.0" in command_bytes


class TestCommandWriterMessageIdSequence:
    """Tests for message ID sequence in CommandWriter"""

    @pytest.fixture
    def mock_connection_handler(self):
        """Create a mock connection handler"""
        handler = MagicMock()
        handler.send_command_to_keg = AsyncMock(return_value=True)
        return handler

    def test_sequential_commands_have_different_ids(self, mock_connection_handler):
        """Test that sequential commands have different message IDs"""
        writer = CommandWriter(mock_connection_handler)

        run_async(writer.send_command("device", Commands.SET_MODE, "1"))
        run_async(writer.send_command("device", Commands.SET_UNIT, "1"))
        run_async(writer.send_command("device", Commands.SET_MEASURE_UNIT, "1"))

        # Extract message IDs from the calls
        msg_ids = []
        for call in mock_connection_handler.send_command_to_keg.call_args_list:
            command_bytes = call[0][1]
            _, msg_id, _ = struct.unpack('>BHH', command_bytes[:5])
            msg_ids.append(msg_id)

        # All message IDs should be unique
        assert len(msg_ids) == len(set(msg_ids))
        assert msg_ids == [1, 2, 3]
