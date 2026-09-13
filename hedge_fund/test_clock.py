"""market_today tests — the market's date, not the machine's.

The provider 400s on any end_date newer than its own today, so the one
property that matters here is direction: this must never come out ahead of
New York.
"""

import sys
import types
from datetime import date, datetime, timezone

import pytest

from hedge_fund import clock
from hedge_fund.clock import _local_date, market_today


def test_market_today_never_runs_past_utc():
    assert market_today() <= datetime.now(timezone.utc).date()


def test_date_flips_at_midnight_in_new_york():
    # EDT is UTC-4: 03:00Z on the 14th is still 23:00 on the 13th in New York.
    assert _local_date(datetime(2026, 9, 14, 3, 0, tzinfo=timezone.utc)) == date(2026, 9, 13)
    assert _local_date(datetime(2026, 9, 14, 4, 0, tzinfo=timezone.utc)) == date(2026, 9, 14)


def test_eastern_offset_follows_dst():
    # EST is UTC-5, so January's flip lands an hour later than September's.
    assert _local_date(datetime(2026, 1, 15, 4, 0, tzinfo=timezone.utc)) == date(2026, 1, 14)
    assert _local_date(datetime(2026, 1, 15, 5, 0, tzinfo=timezone.utc)) == date(2026, 1, 15)


def test_fallback_never_leads_the_tz_database(monkeypatch):
    """Without a tz database the offset is resolved from the DST rule. It may
    lag the true date across a boundary, but leading it is the bug."""
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        eastern = zoneinfo.ZoneInfo(clock._TZ_NAME)
    except Exception:
        pytest.skip("no tz database on this machine")

    class _Unavailable:
        def __init__(self, *_args, **_kwargs):
            raise ValueError("no tz database")

    monkeypatch.setitem(sys.modules, "zoneinfo",
                        types.SimpleNamespace(ZoneInfo=_Unavailable))

    instants = [
        datetime(2026, month, day, hour, tzinfo=timezone.utc)
        for month, day in ((1, 15), (7, 15), (3, 8), (11, 1))  # incl. both DST edges
        for hour in range(3, 9)
    ]
    for t in instants:
        expected = t.astimezone(eastern).date()
        got = clock._local_date(t)
        assert got <= expected, f"{t}: fallback said {got}, New York is {expected}"
