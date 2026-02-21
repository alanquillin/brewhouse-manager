"""Tests for plaato_protocol module"""

import pytest

from lib.devices.plaato_keg.blynk_protocol import BlynkCommand, BlynkMessage
from lib.devices.plaato_keg.plaato_protocol import PlaatoMessage, PlaatoPin, _decode, _decode_internal, decode, decode_list, validate_and_pad_1_and_2


class TestPlaatoPin:
    """Tests for PlaatoPin enum"""

    def test_pin_values(self):
        """Test that pin values are correct"""
        assert PlaatoPin.PERCENT_BEER_LEFT == 48
        assert PlaatoPin.AMOUNT_LEFT == 51
        assert PlaatoPin.TEMPERATURE == 56
        assert PlaatoPin.UNIT == 71
        assert PlaatoPin.MEASURE_UNIT == 75
        assert PlaatoPin.MODE == 88
        assert PlaatoPin.FIRMWARE_VERSION == 93


class TestValidateAndPad1And2:
    """Tests for validate_and_pad_1_and_2 function"""

    def test_valid_single_digit_1(self):
        """Test padding single digit 1"""
        result = validate_and_pad_1_and_2("1")
        assert result == "01"

    def test_valid_single_digit_2(self):
        """Test padding single digit 2"""
        result = validate_and_pad_1_and_2("2")
        assert result == "02"

    def test_valid_already_padded_01(self):
        """Test already padded 01"""
        result = validate_and_pad_1_and_2("01")
        assert result == "01"

    def test_valid_already_padded_02(self):
        """Test already padded 02"""
        result = validate_and_pad_1_and_2("02")
        assert result == "02"

    def test_invalid_value(self):
        """Test invalid value returns None"""
        result = validate_and_pad_1_and_2("03")
        assert result is None

    def test_invalid_value_single_digit(self):
        """Test invalid single digit returns None"""
        result = validate_and_pad_1_and_2("5")
        assert result is None

    def test_empty_string(self):
        """Test empty string returns None"""
        result = validate_and_pad_1_and_2("")
        assert result is None

    def test_none_value(self):
        """Test None value returns None"""
        result = validate_and_pad_1_and_2(None)
        assert result is None


class TestPlaatoMessage:
    """Tests for PlaatoMessage class"""

    def test_init(self):
        """Test PlaatoMessage initialization"""
        blynk_msg = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=1, length=10, body=b"vw\x0048\x0050")
        msg = PlaatoMessage(blynk_msg, kind="vw", id_val="48", data="50")

        assert msg.command == BlynkCommand.HARDWARE
        assert msg.msg_id == 1
        assert msg.kind == "vw"
        assert msg.id_val == "48"
        assert msg.data == "50"

    def test_repr_response(self):
        """Test __repr__ for response message"""
        blynk_msg = BlynkMessage(command=BlynkCommand.RESPONSE, msg_id=1, status=200)
        msg = PlaatoMessage(blynk_msg, data="some data")

        repr_str = repr(msg)
        assert "RESPONSE" in repr_str

    def test_repr_command(self):
        """Test __repr__ for command message"""
        blynk_msg = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=1, length=10)
        msg = PlaatoMessage(blynk_msg, kind="vw", id_val="48", data="50")

        repr_str = repr(msg)
        assert "kind=vw" in repr_str
        assert "id_val=48" in repr_str


class TestDecodeInternal:
    """Tests for _decode_internal function"""

    def test_decode_internal_properties(self):
        """Test decoding internal message with key-value pairs"""
        body = b"ver\x001.0.0\x00dev\x00plaato"
        blynk_msg = BlynkMessage(command=BlynkCommand.INTERNAL, msg_id=1, length=len(body), body=body)

        result = _decode_internal(blynk_msg)

        assert result.kind == "not_relevant"
        assert result.id_val == "not_relevant"
        assert isinstance(result.data, dict)
        assert result.data.get("ver") == "1.0.0"
        assert result.data.get("dev") == "plaato"

    def test_decode_internal_odd_parts(self):
        """Test decoding internal message with odd number of parts"""
        body = b"key1\x00value1\x00key2"  # Missing value for key2
        blynk_msg = BlynkMessage(command=BlynkCommand.INTERNAL, msg_id=1, length=len(body), body=body)

        result = _decode_internal(blynk_msg)

        # Should only have key1/value1 pair
        assert result.data.get("key1") == "value1"
        assert "key2" not in result.data


class TestDecodeStandard:
    """Tests for _decode function"""

    def test_decode_hardware_three_parts(self):
        """Test decoding hardware message with three parts"""
        body = b"vw\x0048\x0075.5"
        blynk_msg = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=1, length=len(body), body=body)

        result = _decode(blynk_msg)

        assert result.kind == "vw"
        assert result.id_val == "48"
        assert result.data == "75.5"

    def test_decode_single_part(self):
        """Test decoding message with single part"""
        body = b"deviceid123"
        blynk_msg = BlynkMessage(command=BlynkCommand.GET_SHARED_DASH, msg_id=1, length=len(body), body=body)

        result = _decode(blynk_msg)

        assert result.kind == "not_relevant"
        assert result.id_val == "not_relevant"
        assert result.data == "deviceid123"

    def test_decode_ping(self):
        """Test decoding PING message returns PlaatoMessage without processing"""
        blynk_msg = BlynkMessage(command=BlynkCommand.PING, msg_id=1, length=0, body=b"")

        result = _decode(blynk_msg)

        assert result.command == BlynkCommand.PING
        assert result.kind is None
        assert result.id_val is None

    def test_decode_notify(self):
        """Test decoding NOTIFY message"""
        blynk_msg = BlynkMessage(command=BlynkCommand.NOTIFY, msg_id=1, length=0, body=b"")

        result = _decode(blynk_msg)

        assert result.command == BlynkCommand.NOTIFY

    def test_decode_property(self):
        """Test decoding PROPERTY message"""
        body = b"51\x00max\x00100"
        blynk_msg = BlynkMessage(command=BlynkCommand.PROPERTY, msg_id=1, length=len(body), body=body)

        result = _decode(blynk_msg)

        assert result.kind == "51"
        assert result.id_val == "max"
        assert result.data == "100"


class TestDecode:
    """Tests for decode function"""

    def test_decode_internal_routes_correctly(self):
        """Test that INTERNAL command routes to _decode_internal"""
        body = b"key\x00value"
        blynk_msg = BlynkMessage(command=BlynkCommand.INTERNAL, msg_id=1, length=len(body), body=body)

        result = decode(blynk_msg)

        assert isinstance(result.data, dict)

    def test_decode_hardware_routes_correctly(self):
        """Test that HARDWARE command routes to _decode"""
        body = b"vw\x0048\x0050"
        blynk_msg = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=1, length=len(body), body=body)

        result = decode(blynk_msg)

        assert result.kind == "vw"


class TestDecodeList:
    """Tests for decode_list function"""

    def test_decode_list_multiple_messages(self):
        """Test decoding a list of messages"""
        body1 = b"vw\x0048\x0050"
        msg1 = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=1, length=len(body1), body=body1)

        body2 = b"vw\x0051\x00100"
        msg2 = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=2, length=len(body2), body=body2)

        results = decode_list([msg1, msg2])

        assert len(results) == 2
        assert results[0].id_val == "48"
        assert results[1].id_val == "51"

    def test_decode_list_empty(self):
        """Test decoding empty list"""
        results = decode_list([])
        assert results == []

    def test_decode_list_mixed_types(self):
        """Test decoding list with mixed message types"""
        internal_body = b"ver\x001.0"
        internal_msg = BlynkMessage(command=BlynkCommand.INTERNAL, msg_id=1, length=len(internal_body), body=internal_body)

        hardware_body = b"vw\x0048\x0050"
        hardware_msg = BlynkMessage(command=BlynkCommand.HARDWARE, msg_id=2, length=len(hardware_body), body=hardware_body)

        results = decode_list([internal_msg, hardware_msg])

        assert len(results) == 2
        assert isinstance(results[0].data, dict)  # Internal message
        assert results[1].kind == "vw"  # Hardware message
