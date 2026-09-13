"""What day it is, in the market's timezone.

"Today" for this program is today in New York, not today on the machine
running it. The data provider rejects any request whose ``end_date`` is newer
than its own today — ``end_date must be today (YYYY-MM-DD) or older`` — and it
fronts a US market feed, so a laptop in UTC+8 at 00:30 local time would name a
date the provider has not reached, and the first price fetch of the cycle
would 400.

Erring early is free, erring late is a hard failure. A stale ``end_date`` is
always accepted, and every lookback here is wide enough (seven days for
marks, weeks for a backtest) that one extra day of age changes nothing. New
York is the earliest date any reading of "today" can produce — it is at most
UTC, never past it — so it can only ever come out too old, never too new.

Textual-free and import-light on purpose: the CLI, the TUI, and the backtester
all need this, and nothing here may import them back.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

_TZ_NAME = "America/New_York"


def market_today() -> date:
    """Today's date in the market's timezone, US/Eastern."""
    return _local_date(datetime.now(timezone.utc))


def _local_date(now: datetime) -> date:
    """The date in New York at *now* (a UTC datetime)."""
    try:
        from zoneinfo import ZoneInfo

        return now.astimezone(ZoneInfo(_TZ_NAME)).date()
    except Exception:
        # No tz database. That should not happen in practice — zoneinfo needs
        # one and it arrives with pandas' tzdata dependency — so this is
        # belt-and-braces. Resolve both Eastern offsets and take the earlier:
        # the result can lag the true New York date, but only across a
        # boundary where no new bar can exist anyway, while leading it would
        # name a day the provider has not reached.
        return min((now + timedelta(hours=o)).date() for o in (-4, -5))
