"""Cohort week calculation — single source of truth.

The cohort is the Monday of the ISO week in which the lead was created,
evaluated in Pacific time. Stored as YYYY-MM-DD.

Example: a lead created Wednesday 2026-04-15 at 2pm PT has cohort
2026-04-13 (the Monday of that week).
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")


def cohort_for_iso_timestamp(iso_ts: str) -> str:
    """Given an ISO-8601 UTC timestamp from Close, return the cohort
    Monday as YYYY-MM-DD in Pacific time.

    Close returns timestamps like '2026-04-15T21:30:00.000000+00:00'.
    """
    # Handle trailing Z just in case; Close uses +00:00 but be defensive
    dt_utc = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    dt_pacific = dt_utc.astimezone(PACIFIC)
    # weekday(): Monday=0, Sunday=6
    monday = dt_pacific - timedelta(days=dt_pacific.weekday())
    return monday.strftime("%Y-%m-%d")
