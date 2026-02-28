from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from automation.sites import SiteRuntimeInput, run_single_site_download


@dataclass
class SiteConfig:
    name: str
    flow_type: str
    supports_range: bool
    monday_daily_only: bool
    stores: list[str]
    login_url: str
    selectors: dict[str, str]
    username_env: str
    username_value: str
    password_env: str
    retries: int
    query_type_value: str
    query_opens_popup: bool


def setup_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("downloader")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


def get_target_dates(run_date: dt.date) -> list[dt.date]:
    if run_date.weekday() == 0:  # Monday
        return [run_date - dt.timedelta(days=3), run_date - dt.timedelta(days=2), run_date - dt.timedelta(days=1)]
    return [run_date - dt.timedelta(days=1)]


def _build_store_list(item: dict) -> list[str]:
    if item.get("stores"):
        return [str(s) for s in item["stores"]]

    start = item.get("store_range_start")
    end = item.get("store_range_end")
    if start is None or end is None:
        return []

    width = int(item.get("store_range_width", 2))
    return [str(i).zfill(width) for i in range(int(start), int(end) + 1)]


def _read_config(config_path: Path) -> dict:
    if config_path.suffix.lower() == ".json":
        return json.loads(config_path.read_text(encoding="utf-8"))

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - depends on runtime env
        raise RuntimeError("pyyaml is required for YAML config. Or use --config *.json for dry-run tests.") from exc
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def load_sites(config_path: Path) -> list[SiteConfig]:
    data = _read_config(config_path)
    sites = []
    for item in data.get("sites", []):
        sites.append(
            SiteConfig(
                name=item["name"],
                flow_type=item["flow_type"],
                supports_range=item.get("supports_range", False),
                monday_daily_only=item.get("monday_daily_only", False),
                stores=_build_store_list(item),
                login_url=item["login_url"],
                selectors=item["selectors"],
                username_env=item.get("username_env", "SITE_USERNAME"),
                username_value=item.get("username_value", ""),
                password_env=item.get("password_env", "SITE_PASSWORD"),
                retries=item.get("retries", 2),
                query_type_value=item.get("query_type_value", ""),
                query_opens_popup=item.get("query_opens_popup", False),
            )
        )
    return sites


def daterange_text(dates: list[dt.date]) -> str:
    if len(dates) == 1:
        return dates[0].isoformat()
    return f"{dates[0].isoformat()} ~ {dates[-1].isoformat()}"


def planned_download_units(site: SiteConfig, dates: list[dt.date]) -> Iterable[tuple[list[dt.date], str]]:
    if len(dates) > 1 and site.supports_range and not site.monday_daily_only:
        for store in site.stores:
            yield (dates, store)
    else:
        for d in dates:
            for store in site.stores:
                yield ([d], store)


def run_site_download(
    site: SiteConfig,
    date_group: list[dt.date],
    store: str,
    output_dir: Path,
    logger: logging.Logger,
    headless: bool,
    dry_run: bool,
) -> tuple[bool, str]:
    if dry_run:
        return True, f"dry-run planned store={store} date={daterange_text(date_group)}"

    username = site.username_value or os.getenv(site.username_env, "")
    password = os.getenv(site.password_env, "")
    if not username or not password:
        return False, f"missing credentials: username({site.username_env} or username_value)/password({site.password_env})"

    runtime = SiteRuntimeInput(
        name=site.name,
        login_url=site.login_url,
        username=username,
        password=password,
        username_selector=site.selectors["username"],
        password_selector=site.selectors["password"],
        submit_selector=site.selectors["submit"],
        date_from_selector=site.selectors["date_from"],
        date_to_selector=site.selectors.get("date_to"),
        store_selector=site.selectors["store"],
        query_selector=site.selectors.get("query"),
        query_type_selector=site.selectors.get("query_type"),
        query_type_value=site.query_type_value,
        file_link_selector=site.selectors.get("file_link"),
        download_selector=site.selectors["download"],
        flow_type=site.flow_type,
        query_opens_popup=site.query_opens_popup,
        headless=headless,
    )

    for attempt in range(1, site.retries + 2):
        ok, message = run_single_site_download(runtime, date_group, store, output_dir)
        if ok:
            return True, message
        logger.warning(
            "[%s] attempt=%s failed store=%s date=%s msg=%s",
            site.name,
            attempt,
            store,
            daterange_text(date_group),
            message,
        )
    return False, message


def write_result_csv(csv_path: Path, rows: list[dict[str, str]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["site", "store", "date_group", "status", "message"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="多网站数据自动下载任务")
    parser.add_argument("--config", default="automation/config/sites.example.yaml", help="站点配置 YAML/JSON")
    parser.add_argument("--run-date", default=dt.date.today().isoformat(), help="运行日期（YYYY-MM-DD）")
    parser.add_argument("--download-root", default="downloads", help="下载根目录")
    parser.add_argument("--headful", action="store_true", help="使用有界面浏览器（调试站点时建议开启）")
    parser.add_argument("--dry-run", action="store_true", help="仅验证日期和任务拆分，不访问网站")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_date = dt.date.fromisoformat(args.run_date)
    folder_name = run_date.strftime("%y%m%d")

    output_dir = Path(args.download_root) / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = Path("logs") / f"{run_date.isoformat()}.log"
    logger = setup_logger(log_file)

    target_dates = get_target_dates(run_date)
    sites = load_sites(Path(args.config))

    logger.info("run_date=%s target_dates=%s output_dir=%s dry_run=%s", run_date, [d.isoformat() for d in target_dates], output_dir, args.dry_run)

    result_rows: list[dict[str, str]] = []
    for site in sites:
        for date_group, store in planned_download_units(site, target_dates):
            ok, message = run_site_download(site, date_group, store, output_dir, logger, headless=not args.headful, dry_run=args.dry_run)
            result_rows.append(
                {
                    "site": site.name,
                    "store": store,
                    "date_group": daterange_text(date_group),
                    "status": "success" if ok else "failed",
                    "message": message,
                }
            )

    result_csv = Path("logs") / f"result_{run_date.strftime('%Y%m%d')}.csv"
    write_result_csv(result_csv, result_rows)
    logger.info("finished summary_csv=%s", result_csv)

    failed = sum(1 for r in result_rows if r["status"] == "failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
