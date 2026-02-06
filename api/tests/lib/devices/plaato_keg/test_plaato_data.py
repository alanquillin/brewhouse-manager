"""Tests for plaato_data module"""

import pytest

from lib.devices.plaato_keg.blynk_protocol import BlynkCommand, BlynkMessage
from lib.devices.plaato_keg.plaato_protocol import PlaatoPin, PlaatoMessage
from lib.devices.plaato_keg.plaato_data import (
    PLAATO_DATA_MAP,
    USER_OVERRIDEABLE,
    decode,
    decode_list,
    _decode_hardware_property,
)


class TestUserOverrideable:
    """Tests for USER_OVERRIDEABLE mapping"""

    def test_unit_mapping(self):
        """Test UNIT pin is mapped correctly"""
        assert str(PlaatoPin.UNIT) in USER_OVERRIDEABLE
        assert USER_OVERRIDEABLE[str(PlaatoPin.UNIT)] == "user_unit"

    def test_measure_unit_mapping(self):
        """Test MEASURE_UNIT pin is mapped correctly"""
        assert str(PlaatoPin.MEASURE_UNIT) in USER_OVERRIDEABLE
        assert USER_OVERRIDEABLE[str(PlaatoPin.MEASURE_UNIT)] == "user_measure_unit"

    def test_mode_mapping(self):
        """Test MODE pin is mapped correctly"""
        assert str(PlaatoPin.MODE) in USER_OVERRIDEABLE
        assert USER_OVERRIDEABLE[str(PlaatoPin.MODE)] == "user_keg_mode_c02_beer"


class TestPlaatoDataMap:
    """Tests for PLAATO_DATA_MAP"""

    def test_percent_beer_left_mapping(self):
        """Test percent beer left is mapped"""
        key = ("hardware", "vw", str(PlaatoPin.PERCENT_BEER_LEFT))
        assert key in PLAATO_DATA_MAP
        assert PLAATO_DATA_MAP[key] == "percent_of_beer_left"

    def test_amount_left_mapping(self):
        """Test amount left is mapped"""
        key = ("hardware", "vw", str(PlaatoPin.AMOUNT_LEFT))
        assert key in PLAATO_DATA_MAP
        assert PLAATO_DATA_MAP[key] == "amount_left"

    def test_temperature_mapping(self):
        """Test temperature is mapped"""
        key = ("hardware", "vw", str(PlaatoPin.TEMPERATURE))
        assert key in PLAATO_DATA_MAP
        assert PLAATO_DATA_MAP[key] == "keg_temperature"

    def test_firmware_version_mapping(self):
        """Test firmware version is mapped"""
        key = ("hardware", "vw", str(PlaatoPin.FIRMWARE_VERSION))
        assert key in PLAATO_DATA_MAP
        assert PLAATO_DATA_MAP[key] == "firmware_version"

    def test_property_max_keg_volume_mapping(self):
        """Test property max keg volume is mapped"""
        key = ("property", "51", "max")
        assert key in PLAATO_DATA_MAP
        assert PLAATO_DATA_MAP[key] == "max_keg_volume"


class TestDecodeHardwareProperty:
    """Tests for _decode_hardware_property function"""

    def test_decode_known_hardware_pin(self):
        """Test decoding a known hardware pin"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=10,
            body=b"test"
        )
        plaato_msg = PlaatoMessage(
            blynk_msg,
            kind="vw",
            id_val=str(PlaatoPin.PERCENT_BEER_LEFT),
            data="75.5"
        )

        result = _decode_hardware_property(plaato_msg)

        assert result is not None
        assert result[0] == "percent_of_beer_left"
        assert result[1] == "75.5"
        assert result[2] == str(PlaatoPin.PERCENT_BEER_LEFT)

    def test_decode_known_property_pin(self):
        """Test decoding a known property message"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.PROPERTY,
            msg_id=1,
            length=10,
            body=b"test"
        )
        plaato_msg = PlaatoMessage(
            blynk_msg,
            kind="51",
            id_val="max",
            data="100"
        )

        result = _decode_hardware_property(plaato_msg)

        assert result is not None
        assert result[0] == "max_keg_volume"
        assert result[1] == "100"

    def test_decode_unknown_pin_returns_none(self):
        """Test decoding unknown pin returns None"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=10,
            body=b"test"
        )
        plaato_msg = PlaatoMessage(
            blynk_msg,
            kind="vw",
            id_val="999",  # Unknown pin
            data="value"
        )

        result = _decode_hardware_property(plaato_msg)

        assert result is None

    def test_decode_unknown_pin_with_include_flag(self):
        """Test decoding unknown pin with include_unknown_data=True"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=10,
            body=b"test"
        )
        plaato_msg = PlaatoMessage(
            blynk_msg,
            kind="vw",
            id_val="999",
            data="value"
        )

        result = _decode_hardware_property(plaato_msg, include_unknown_data=True)

        assert result is not None
        assert result[0] == "_hardware_vw_999"
        assert result[1] == "value"


class TestDecode:
    """Tests for decode function"""

    def test_decode_get_shared_dash(self):
        """Test decoding GET_SHARED_DASH returns device id"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.GET_SHARED_DASH,
            msg_id=1,
            length=10,
            body=b"device123"
        )
        plaato_msg = PlaatoMessage(blynk_msg, data="device123", id_val="some_id")

        result = decode(plaato_msg)

        assert result is not None
        assert result[0] == "id"
        assert result[1] == "device123"

    def test_decode_internal(self):
        """Test decoding INTERNAL returns internal data"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.INTERNAL,
            msg_id=1,
            length=10,
            body=b"key\x00value"
        )
        plaato_msg = PlaatoMessage(blynk_msg, data={"key": "value"}, id_val="some_id")

        result = decode(plaato_msg)

        assert result is not None
        assert result[0] == "internal"
        assert result[1] == {"key": "value"}

    def test_decode_hardware(self):
        """Test decoding HARDWARE message"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=10,
            body=b"test"
        )
        plaato_msg = PlaatoMessage(
            blynk_msg,
            kind="vw",
            id_val=str(PlaatoPin.AMOUNT_LEFT),
            data="50.0"
        )

        result = decode(plaato_msg)

        assert result is not None
        assert result[0] == "amount_left"
        assert result[1] == "50.0"

    def test_decode_unknown_command_returns_none(self):
        """Test decoding unknown command returns None"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.PING,
            msg_id=1,
            length=0,
            body=b""
        )
        plaato_msg = PlaatoMessage(blynk_msg)

        result = decode(plaato_msg)

        assert result is None


class TestDecodeList:
    """Tests for decode_list function"""

    def test_decode_list_filters_none(self):
        """Test that decode_list filters out None results"""
        # Known pin - will decode
        blynk_msg1 = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=10,
            body=b"test"
        )
        known_msg = PlaatoMessage(
            blynk_msg1,
            kind="vw",
            id_val=str(PlaatoPin.PERCENT_BEER_LEFT),
            data="75"
        )

        # Unknown pin - will return None
        blynk_msg2 = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=2,
            length=10,
            body=b"test"
        )
        unknown_msg = PlaatoMessage(
            blynk_msg2,
            kind="vw",
            id_val="999",
            data="value"
        )

        # PING - will return None
        blynk_msg3 = BlynkMessage(
            command=BlynkCommand.PING,
            msg_id=3,
            length=0,
            body=b""
        )
        ping_msg = PlaatoMessage(blynk_msg3)

        results = decode_list([known_msg, unknown_msg, ping_msg])

        # Should only contain the known message result
        assert len(results) == 1
        assert results[0][0] == "percent_of_beer_left"

    def test_decode_list_empty(self):
        """Test decode_list with empty list"""
        results = decode_list([])
        assert results == []

    def test_decode_list_all_known(self):
        """Test decode_list with all known messages"""
        blynk_msg1 = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=1,
            length=10,
            body=b"test"
        )
        msg1 = PlaatoMessage(
            blynk_msg1,
            kind="vw",
            id_val=str(PlaatoPin.PERCENT_BEER_LEFT),
            data="75"
        )

        blynk_msg2 = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=2,
            length=10,
            body=b"test"
        )
        msg2 = PlaatoMessage(
            blynk_msg2,
            kind="vw",
            id_val=str(PlaatoPin.AMOUNT_LEFT),
            data="50"
        )

        results = decode_list([msg1, msg2])

        assert len(results) == 2
        assert results[0][0] == "percent_of_beer_left"
        assert results[1][0] == "amount_left"

    def test_decode_list_with_device_id(self):
        """Test decode_list with GET_SHARED_DASH containing device id"""
        blynk_msg = BlynkMessage(
            command=BlynkCommand.GET_SHARED_DASH,
            msg_id=1,
            length=10,
            body=b"device123"
        )
        id_msg = PlaatoMessage(blynk_msg, data="device123", id_val="test")

        blynk_msg2 = BlynkMessage(
            command=BlynkCommand.HARDWARE,
            msg_id=2,
            length=10,
            body=b"test"
        )
        data_msg = PlaatoMessage(
            blynk_msg2,
            kind="vw",
            id_val=str(PlaatoPin.TEMPERATURE),
            data="4.5"
        )

        results = decode_list([id_msg, data_msg])

        assert len(results) == 2
        assert results[0][0] == "id"
        assert results[0][1] == "device123"
        assert results[1][0] == "keg_temperature"
        assert results[1][1] == "4.5"
