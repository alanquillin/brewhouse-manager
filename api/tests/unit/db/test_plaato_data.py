"""Tests for db/plaato_data.py module - PlaatoData model"""

from unittest.mock import MagicMock

import pytest

from db.plaato_data import PlaatoData


class TestPlaatoDataModel:
    """Tests for PlaatoData model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert PlaatoData.__tablename__ == "plaato_data"

    def test_has_core_columns(self):
        """Test model has core columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "last_updated_on" in column_names

    def test_has_pour_data_columns(self):
        """Test model has pour-related columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "last_pour" in column_names
        assert "last_pour_string" in column_names
        assert "is_pouring" in column_names

    def test_has_volume_columns(self):
        """Test model has volume-related columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "amount_left" in column_names
        assert "percent_of_beer_left" in column_names
        assert "max_keg_volume" in column_names
        assert "volume_unit" in column_names
        assert "beer_left_unit" in column_names

    def test_has_temperature_columns(self):
        """Test model has temperature-related columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "keg_temperature" in column_names
        assert "keg_temperature_string" in column_names
        assert "temperature_offset" in column_names
        assert "temperature_unit" in column_names
        assert "min_temperature" in column_names
        assert "max_temperature" in column_names
        assert "chip_temperature_string" in column_names

    def test_has_calibration_columns(self):
        """Test model has calibration-related columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "tare" in column_names
        assert "known_weight_calibrate" in column_names
        assert "empty_keg_weight" in column_names
        assert "sensitivity" in column_names

    def test_has_beer_info_columns(self):
        """Test model has beer info columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "beer_style" in column_names
        assert "og" in column_names
        assert "fg" in column_names
        assert "calculated_abv" in column_names
        assert "calculated_alcohol_string" in column_names

    def test_has_unit_columns(self):
        """Test model has unit-related columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "unit" in column_names
        assert "measure_unit" in column_names
        assert "user_unit" in column_names
        assert "user_measure_unit" in column_names

    def test_has_device_columns(self):
        """Test model has device info columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "wifi_signal_strength" in column_names
        assert "firmware_version" in column_names
        assert "leak_detection" in column_names

    def test_has_keg_mode_columns(self):
        """Test model has keg mode columns"""
        column_names = [col.name for col in PlaatoData.__table__.columns]
        assert "keg_mode_c02_beer" in column_names
        assert "user_keg_mode_c02_beer" in column_names

    def test_inherits_mixins(self):
        """Test PlaatoData inherits required mixins"""
        from db import AsyncQueryMethodsMixin, AuditedMixin, DictifiableMixin

        assert issubclass(PlaatoData, DictifiableMixin)
        assert issubclass(PlaatoData, AuditedMixin)
        assert issubclass(PlaatoData, AsyncQueryMethodsMixin)

    def test_id_is_primary_key(self):
        """Test id is the primary key"""
        id_col = next(c for c in PlaatoData.__table__.columns if c.name == "id")
        assert id_col.primary_key is True

    def test_id_is_string_type(self):
        """Test id is String type (Plaato device ID)"""
        id_col = next(c for c in PlaatoData.__table__.columns if c.name == "id")
        from sqlalchemy import String

        assert isinstance(id_col.type, String)
