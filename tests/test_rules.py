import datetime as dt
import json
from pathlib import Path

from automation.main import SiteConfig, _build_store_list, _read_config, get_target_dates, planned_download_units


def _site(**kwargs):
    base = dict(
        name="s",
        flow_type="query_then_download",
        supports_range=True,
        monday_daily_only=False,
        stores=["a", "b"],
        login_url="https://example.com",
        selectors={
            "username": "#u",
            "password": "#p",
            "submit": "#s",
            "date_from": "#d1",
            "store": "#st",
            "download": "#dl",
        },
        username_env="U",
        username_value="",
        password_env="P",
        retries=1,
        query_type_value="",
        query_opens_popup=False,
    )
    base.update(kwargs)
    return SiteConfig(**base)


def test_monday_dates():
    dates = get_target_dates(dt.date(2025, 2, 17))
    assert [d.isoformat() for d in dates] == ["2025-02-14", "2025-02-15", "2025-02-16"]


def test_non_monday_dates():
    dates = get_target_dates(dt.date(2025, 2, 18))
    assert [d.isoformat() for d in dates] == ["2025-02-17"]


def test_range_planning():
    site = _site(supports_range=True, monday_daily_only=False, stores=["x"])
    dates = [dt.date(2025, 2, 14), dt.date(2025, 2, 15), dt.date(2025, 2, 16)]
    units = list(planned_download_units(site, dates))
    assert len(units) == 1
    assert units[0][1] == "x"
    assert len(units[0][0]) == 3


def test_daily_only_planning():
    site = _site(supports_range=True, monday_daily_only=True, stores=["x"])
    dates = [dt.date(2025, 2, 14), dt.date(2025, 2, 15), dt.date(2025, 2, 16)]
    units = list(planned_download_units(site, dates))
    assert len(units) == 3


def test_build_store_list_from_range():
    item = {"store_range_start": 1, "store_range_end": 3, "store_range_width": 2}
    assert _build_store_list(item) == ["01", "02", "03"]


def test_read_config_json(tmp_path: Path):
    fp = tmp_path / "sites.json"
    payload = {"sites": [{"name": "x"}]}
    fp.write_text(json.dumps(payload), encoding="utf-8")
    assert _read_config(fp)["sites"][0]["name"] == "x"
