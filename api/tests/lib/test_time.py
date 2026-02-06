"""Tests for lib/time.py module"""

import datetime
import pytest

from lib.time import parse_iso8601_utc, utcnow_aware, next_month


class TestParseIso8601Utc:
    """Tests for parse_iso8601_utc function"""

    def test_parse_with_timezone(self):
        """Test parsing ISO string with timezone info"""
        result = parse_iso8601_utc("2024-01-15T10:30:00+00:00")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo is not None

    def test_parse_without_timezone_assumes_utc(self):
        """Test parsing ISO string without timezone assumes UTC"""
        result = parse_iso8601_utc("2024-06-20T14:45:30")
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 20
        assert result.hour == 14
        assert result.minute == 45
        assert result.second == 30
        assert result.tzinfo == datetime.timezone.utc

    def test_parse_date_only(self):
        """Test parsing date-only ISO string"""
        result = parse_iso8601_utc("2024-03-10")
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 10
        assert result.tzinfo == datetime.timezone.utc

    def test_parse_with_microseconds(self):
        """Test parsing ISO string with microseconds"""
        result = parse_iso8601_utc("2024-01-15T10:30:00.123456")
        assert result.microsecond == 123456


class TestUtcnowAware:
    """Tests for utcnow_aware function"""

    def test_returns_datetime(self):
        """Test that utcnow_aware returns a datetime"""
        result = utcnow_aware()
        assert isinstance(result, datetime.datetime)

    def test_returns_aware_datetime(self):
        """Test that utcnow_aware returns timezone-aware datetime"""
        result = utcnow_aware()
        assert result.tzinfo is not None
        assert result.tzinfo == datetime.timezone.utc

    def test_returns_current_time(self):
        """Test that utcnow_aware returns approximately current time"""
        before = datetime.datetime.utcnow()
        result = utcnow_aware()
        after = datetime.datetime.utcnow()

        # Remove tzinfo for comparison
        result_naive = result.replace(tzinfo=None)
        assert before <= result_naive <= after


class TestNextMonth:
    """Tests for next_month function"""

    def test_next_month_from_january(self):
        """Test next_month from January goes to February"""
        jan_15 = datetime.datetime(2024, 1, 15, tzinfo=datetime.timezone.utc)
        result = next_month(jan_15)
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 15

    def test_next_month_from_december(self):
        """Test next_month from December goes to January of next year"""
        dec_10 = datetime.datetime(2024, 12, 10, tzinfo=datetime.timezone.utc)
        result = next_month(dec_10)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 10

    def test_next_month_saturates_day(self):
        """Test next_month saturates day at end of month (1/31 -> 2/28)"""
        jan_31 = datetime.datetime(2024, 1, 31, tzinfo=datetime.timezone.utc)
        result = next_month(jan_31)
        assert result.year == 2024
        assert result.month == 2
        # 2024 is a leap year, so Feb has 29 days
        assert result.day == 29

    def test_next_month_saturates_non_leap_year(self):
        """Test next_month saturates day in non-leap year"""
        jan_31 = datetime.datetime(2023, 1, 31, tzinfo=datetime.timezone.utc)
        result = next_month(jan_31)
        assert result.year == 2023
        assert result.month == 2
        assert result.day == 28  # Non-leap year

    def test_next_month_no_base_day_uses_current(self):
        """Test next_month with no base_day uses current time"""
        result = next_month()
        now = utcnow_aware()

        # Result should be roughly one month from now
        assert result > now
        # Could be same month (if day > 28) or next month
        if now.month == 12:
            assert result.month == 1 and result.year == now.year + 1
        else:
            assert result.month >= now.month
