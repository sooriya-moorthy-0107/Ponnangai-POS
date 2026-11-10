import os
import time
from datetime import datetime, date, time as dt_time, timedelta, timezone

# Standardize application timezone to Indian Standard Time (IST, UTC+5:30)
os.environ["TZ"] = "Asia/Kolkata"
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass

# Fallback-safe IST timezone definition (UTC +5:30)
try:
    import zoneinfo
    IST = zoneinfo.ZoneInfo("Asia/Kolkata")
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_now() -> datetime:
    """Returns the current date and time in Indian Standard Time (naive datetime for DB)."""
    return datetime.now(IST).replace(tzinfo=None)


def get_ist_today_range() -> tuple[datetime, datetime]:
    """Returns (start_of_day, end_of_day) in IST."""
    ist_now = get_ist_now()
    start = datetime.combine(ist_now.date(), dt_time.min)
    end = datetime.combine(ist_now.date(), dt_time.max)
    return start, end


def format_ist_iso(dt: datetime | None) -> str:
    """Formats datetime as ISO-8601 with explicit IST +05:30 offset so browsers never misinterpret it."""
    if not dt:
        return ""
    # Ensure format YYYY-MM-DDTHH:MM:SS.ffffff+05:30
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"


def format_ist_time(dt: datetime | None, fmt: str = "%I:%M %p") -> str:
    """Formats datetime in 12-hour AM/PM format (e.g. 01:30 PM)."""
    if not dt:
        return ""
    return dt.strftime(fmt)


def format_ist_datetime(dt: datetime | None, fmt: str = "%Y-%m-%d %I:%M %p") -> str:
    """Formats full datetime in IST (e.g. 2026-11-10 01:30 PM)."""
    if not dt:
        return ""
    return dt.strftime(fmt)

