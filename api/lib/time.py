import datetime

from dateutil import relativedelta


def parse_iso8601_utc(in_str):

    """Parse an isoformat()'d str assuming UTC if no tzinfo is provided."""

    timestamp = datetime.datetime.fromisoformat(in_str)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

    return timestamp


def utcnow_aware():

    """Return an aware datetime in UTC."""

    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


def next_month(base_day=None):

    """Return base_day or today +1 month, saturating at the end of the month e.g. 1/31 -> 2/28."""

    return (base_day or utcnow_aware()) + relativedelta.relativedelta(months=1)
