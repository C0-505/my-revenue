from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import urllib.error
import urllib.request

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cafeteria popup reminder with optional Feishu push")
    parser.add_argument("--menu-file", default=str(Path(__file__).resolve().parent / "menu.json"), help="Path to menu JSON")
    parser.add_argument("--date", default=os.getenv("CAFETERIA_TEST_DATE", ""), help="Override date in YYYY-MM-DD")
    parser.add_argument("--no-popup", action="store_true", help="Send Feishu only, do not show local popup")
    return parser.parse_args()


def load_config(menu_file: Path) -> tuple[dict[str, dict[str, str]], dict[str, object]]:
    with menu_file.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if "dates" in data and isinstance(data["dates"], dict):
        dates = data["dates"]
        feishu = data.get("feishu", {}) if isinstance(data.get("feishu", {}), dict) else {}
    else:
        dates = data
        feishu = {}

    normalized: dict[str, dict[str, str]] = {}
    for date_key, menu in dates.items():
        if not isinstance(menu, dict):
            continue
        lunch = str(menu.get("lunch", "")).strip()
        dinner = str(menu.get("dinner", "")).strip()
        if lunch or dinner:
            normalized[str(date_key)] = {"lunch": lunch, "dinner": dinner}
    return normalized, feishu


def build_content(date_str: str, menu: dict[str, str]) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = WEEKDAY_CN[date_obj.weekday()]
    date_text = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
    lunch = menu.get("lunch", "") or "（未配置）"
    dinner = menu.get("dinner", "") or "（未配置）"
    return f"{date_text}（{weekday}）食堂菜单\n\n午餐：{lunch}\n晚餐：{dinner}"


def resolve_webhook(feishu_cfg: dict[str, object]) -> str:
    env_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if env_url:
        return env_url
    enabled = bool(feishu_cfg.get("enabled", False))
    cfg_url = str(feishu_cfg.get("webhook_url", "")).strip()
    if enabled and cfg_url:
        return cfg_url
    return ""


def send_feishu_text(text: str, webhook_url: str) -> None:
    payload = json.dumps(
        {"msg_type": "text", "content": {"text": f"【食堂餐品提醒】\n{text}"}},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


def show_popup(text: str) -> None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo("食堂餐品提醒", text, parent=root)
    root.destroy()


def main() -> None:
    args = parse_args()
    menu_file = Path(args.menu_file)
    if not menu_file.exists():
        return

    menu_by_date, feishu_cfg = load_config(menu_file)
    today = args.date.strip() or datetime.now().strftime("%Y-%m-%d")
    menu = menu_by_date.get(today)
    if not menu:
        return

    content = build_content(today, menu)
    webhook = resolve_webhook(feishu_cfg)
    if webhook:
        try:
            send_feishu_text(content, webhook)
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass

    if not args.no_popup:
        show_popup(content)


if __name__ == "__main__":
    main()
