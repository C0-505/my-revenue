from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


@dataclass
class SiteConfig:
    name: str
    flow_type: str
    supports_range: bool
    monday_daily_only: bool
    stores: list[str]


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
    """工作日规则：周一下载上周五~周日，其余工作日下载前一天。"""
    if run_date.weekday() == 0:  # Monday
        return [run_date - dt.timedelta(days=3), run_date - dt.timedelta(days=2), run_date - dt.timedelta(days=1)]
    return [run_date - dt.timedelta(days=1)]


def load_sites(config_path: Path) -> list[SiteConfig]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    sites = []
    for item in data.get("sites", []):
        sites.append(
            SiteConfig(
                name=item["name"],
                flow_type=item["flow_type"],
                supports_range=item.get("supports_range", False),
                monday_daily_only=item.get("monday_daily_only", False),
                stores=item.get("stores", []),
            )
        )
    return sites


def daterange_text(dates: list[dt.date]) -> str:
    if len(dates) == 1:
        return dates[0].isoformat()
    return f"{dates[0].isoformat()} ~ {dates[-1].isoformat()}"


def planned_download_units(site: SiteConfig, dates: list[dt.date]) -> Iterable[tuple[list[dt.date], str]]:
    """返回下载任务颗粒度：(日期列表, 门店)。"""
    if len(dates) > 1 and site.supports_range and not site.monday_daily_only:
        for store in site.stores:
            yield (dates, store)
    else:
        for d in dates:
            for store in site.stores:
                yield ([d], store)


def run_site_download(site: SiteConfig, date_group: list[dt.date], store: str, output_dir: Path, logger: logging.Logger) -> bool:
    """
    这里保留站点流程占位，后续将 Playwright 步骤填入。
    flow_type 参考：
      - query_then_download
      - query_open_file_then_download
      - direct_download
    """
    logger.info("[%s] start store=%s date=%s flow=%s", site.name, store, daterange_text(date_group), site.flow_type)

    try:
        # TODO: 在这里接入 Playwright 自动化步骤
        # 1) 登录
        # 2) 输入日期/门店
        # 3) 点击查询（如需要）
        # 4) 点击下载或先打开结果文件再下载
        # 5) 校验输出目录有新文件
        _ = output_dir
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] failed store=%s date=%s err=%s", site.name, store, daterange_text(date_group), exc)
        return False


def write_result_csv(csv_path: Path, rows: list[dict[str, str]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["site", "store", "date_group", "status", "message"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="多网站数据自动下载任务骨架")
    parser.add_argument("--config", default="automation/config/sites.example.yaml", help="站点配置 YAML")
    parser.add_argument("--run-date", default=dt.date.today().isoformat(), help="运行日期（YYYY-MM-DD）")
    parser.add_argument("--download-root", default="downloads", help="下载根目录")
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

    logger.info("run_date=%s target_dates=%s output_dir=%s", run_date, [d.isoformat() for d in target_dates], output_dir)

    result_rows: list[dict[str, str]] = []
    for site in sites:
        for date_group, store in planned_download_units(site, target_dates):
            ok = run_site_download(site, date_group, store, output_dir, logger)
            result_rows.append(
                {
                    "site": site.name,
                    "store": store,
                    "date_group": daterange_text(date_group),
                    "status": "success" if ok else "failed",
                    "message": "",
                }
            )

    result_csv = Path("logs") / f"result_{run_date.strftime('%Y%m%d')}.csv"
    write_result_csv(result_csv, result_rows)
    logger.info("finished summary_csv=%s", result_csv)

    failed = sum(1 for r in result_rows if r["status"] == "failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
