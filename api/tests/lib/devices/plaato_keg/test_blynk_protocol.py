"""Tests for blynk_protocol module"""

import struct
import pytest

from lib.devices.plaato_keg.blynk_protocol import (
    BlynkCommand,
    BlynkStatus,
    BlynkMessage,
    decode,
    encode_command,
    encode_response,
    response_success,
)


class TestBlynkCommand:
    """Tests for BlynkCommand enum"""

    def test_command_values(self):
        """Test that command values are correct"""
        assert BlynkCommand.RESPONSE == 0
        assert BlynkCommand.HARDWARE == 20
        assert BlynkCommand.INTERNAL == 17
        assert BlynkCommand.PROPERTY == 19
        assert BlynkCommand.GET_SHARED_DASH == 29
        assert BlynkCommand.PING == 6


class TestBlynkStatus:
    """Tests for BlynkStatus enum"""

    def test_status_values(self):
        """Test that status values are correct"""
        assert BlynkStatus.SUCCESS == 200
        assert BlynkStatus.ILLEGAL_COMMAND == 2
        assert BlynkStatus.NOT_AUTHENTICATED == 5
        assert BlynkStatus.TIMEOUT == 16


class TestBlynkMessage:
    """Tests for BlynkMessage class"""

    def test_init(self):
        """Test BlynkMessage initialization"""
        msg = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=10,
            body=b"test"
        )
        assert msg.command == BlynkCommand.HARDWARE
        assert msg.msg_id == 1
        assert msg.length == 10
        assert msg.body == b"test"
        assert msg.status is None

    def test_repr_response(self):
        """Test __repr__ for response message"""
        msg = BlynkMessage(
            command=BlynkCommand.RESPONSE,
            msg_id=1,
            status=BlynkStatus.SUCCESS
        )
        repr_str = repr(msg)
        assert "RESPONSE" in repr_str
        assert "200" in repr_str or "SUCCESS" in repr_str

    def test_repr_command(self):
        """Test __repr__ for command message"""
        msg = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=4,
            body=b"test"
        )
        repr_str = repr(msg)
        # Command may be shown as enum name or int value
        assert "HARDWARE" in repr_str or "20" in repr_str
        assert "length=4" in repr_str

    def test_len(self):
        """Test __len__ method"""
        msg = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=1, length=10)
        assert len(msg) == 10

    def test_len_no_length(self):
        """Test __len__ returns 0 when no length set (Python requires non-negative)"""
        msg = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=1)
        # Note: __len__ must return >= 0 in Python, so we test direct attribute access
        assert msg.length is None


class TestDecode:
    """Tests for decode function"""

    def test_decode_hardware_message(self):
        """Test decoding a hardware message"""
        # Build a HARDWARE message: cmd=20, msg_id=1, length=7, body="vw\x0048\x0050"
        body = b"vw\x0048\x0050"
        data = struct.pack('>BHH', BlynkCommand.HARDWARE, 1, len(body)) + body

        messages = decode(data)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.command == BlynkCommand.HARDWARE
        assert msg.msg_id == 1
        assert msg.length == len(body)
        assert msg.body == body

    def test_decode_response_message(self):
        """Test decoding a response message"""
        # Response: cmd=0, msg_id=1, status=200 (SUCCESS)
        data = struct.pack('>BHH', BlynkCommand.RESPONSE, 1, BlynkStatus.SUCCESS)

        messages = decode(data)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.command == BlynkCommand.RESPONSE
        assert msg.msg_id == 1
        assert msg.status == BlynkStatus.SUCCESS

    def test_decode_multiple_messages(self):
        """Test decoding multiple messages in sequence"""
        # First message: HARDWARE
        body1 = b"vw\x0048\x0050"
        msg1 = struct.pack('>BHH', BlynkCommand.HARDWARE, 1, len(body1)) + body1

        # Second message: PROPERTY
        body2 = b"51\x00max\x00100"
        msg2 = struct.pack('>BHH', BlynkCommand.PROPERTY, 2, len(body2)) + body2

        data = msg1 + msg2
        messages = decode(data)

        assert len(messages) == 2
        assert messages[0].command == BlynkCommand.HARDWARE
        assert messages[1].command == BlynkCommand.PROPERTY

    def test_decode_internal_message(self):
        """Test decoding an internal message"""
        body = b"ver\x001.0.0\x00dev\x00plaato"
        data = struct.pack('>BHH', BlynkCommand.INTERNAL, 1, len(body)) + body

        messages = decode(data)

        assert len(messages) == 1
        assert messages[0].command == BlynkCommand.INTERNAL
        assert messages[0].body == body

    def test_decode_empty_data(self):
        """Test decoding empty data"""
        messages = decode(b"")
        assert messages == []

    def test_decode_incomplete_header(self):
        """Test decoding with incomplete header (less than 5 bytes)"""
        messages = decode(b"\x14\x00\x01")  # Only 3 bytes
        assert messages == []

    def test_decode_unknown_command(self):
        """Test decoding unknown command value"""
        body = b"test"
        data = struct.pack('>BHH', 99, 1, len(body)) + body  # 99 is not a valid command

        messages = decode(data)

        assert len(messages) == 1
        # Command should be stored as string for unknown values
        assert "unknown" in str(messages[0].command)

    def test_decode_get_shared_dash(self):
        """Test decoding GET_SHARED_DASH message"""
        body = b"abc123deviceid"
        data = struct.pack('>BHH', BlynkCommand.GET_SHARED_DASH, 1, len(body)) + body

        messages = decode(data)

        assert len(messages) == 1
        assert messages[0].command == BlynkCommand.GET_SHARED_DASH


class TestEncodeCommand:
    """Tests for encode_command function"""

    def test_encode_hardware_command(self):
        """Test encoding a hardware command"""
        body = b"vw\x0088\x0001"
        result = encode_command(BlynkCommand.HARDWARE, 1, body)

        # Verify header
        cmd, msg_id, length = struct.unpack('>BHH', result[:5])
        assert cmd == BlynkCommand.HARDWARE
        assert msg_id == 1
        assert length == len(body)

        # Verify body
        assert result[5:] == body

    def test_encode_command_with_int(self):
        """Test encoding with integer command value"""
        body = b"test"
        result = encode_command(20, 5, body)  # 20 = HARDWARE

        cmd, msg_id, length = struct.unpack('>BHH', result[:5])
        assert cmd == 20
        assert msg_id == 5
        assert length == len(body)

    def test_encode_empty_body(self):
        """Test encoding with empty body"""
        result = encode_command(BlynkCommand.PING, 1)

        cmd, msg_id, length = struct.unpack('>BHH', result[:5])
        assert cmd == BlynkCommand.PING
        assert length == 0
        assert len(result) == 5


class TestEncodeResponse:
    """Tests for encode_response function"""

    def test_encode_success_response(self):
        """Test encoding a success response"""
        result = encode_response(1, BlynkStatus.SUCCESS)

        cmd, msg_id, status, length = struct.unpack('>BHHH', result[:7])
        assert cmd == 0  # Response command
        assert msg_id == 1
        assert status == BlynkStatus.SUCCESS
        assert length == 0

    def test_encode_response_with_body(self):
        """Test encoding response with body"""
        body = b"error details"
        result = encode_response(2, BlynkStatus.ILLEGAL_COMMAND, body)

        cmd, msg_id, status, length = struct.unpack('>BHHH', result[:7])
        assert cmd == 0
        assert status == BlynkStatus.ILLEGAL_COMMAND
        assert length == len(body)
        assert result[7:] == body

    def test_encode_response_with_int_status(self):
        """Test encoding response with integer status"""
        result = encode_response(1, 200)

        _, _, status, _ = struct.unpack('>BHHH', result[:7])
        assert status == 200


class TestResponseSuccess:
    """Tests for response_success function"""

    def test_default_msg_id(self):
        """Test response_success with default msg_id"""
        result = response_success()

        cmd, msg_id, status = struct.unpack('>BHH', result)
        assert cmd == 0
        assert msg_id == 1
        assert status == BlynkStatus.SUCCESS

    def test_custom_msg_id(self):
        """Test response_success with custom msg_id"""
        result = response_success(msg_id=42)

        _, msg_id, status = struct.unpack('>BHH', result)
        assert msg_id == 42
        assert status == BlynkStatus.SUCCESS


class TestRoundTrip:
    """Integration tests for encode/decode round trips"""

    def test_hardware_round_trip(self):
        """Test encoding and decoding a hardware command"""
        original_body = b"vw\x0048\x0075.5"
        encoded = encode_command(BlynkCommand.HARDWARE, 123, original_body)

        messages = decode(encoded)

        assert len(messages) == 1
        assert messages[0].command == BlynkCommand.HARDWARE
        assert messages[0].msg_id == 123
        assert messages[0].body == original_body
