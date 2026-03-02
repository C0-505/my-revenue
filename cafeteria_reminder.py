from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import urllib.error
import urllib.request

BASE_DIR = Path(__file__).resolve().parent
MENU_FILE = BASE_DIR / "menu.json"
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _today_str() -> str:
    # For local testing: set CAFETERIA_TEST_DATE=YYYY-MM-DD
    return os.getenv("CAFETERIA_TEST_DATE") or datetime.now().strftime("%Y-%m-%d")


def _load_config() -> tuple[dict[str, dict[str, str]], dict[str, object]]:
    with MENU_FILE.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Backward compatibility: allow top-level date map.
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


def _build_content(today: str, menu: dict[str, str]) -> str:
    date_obj = datetime.strptime(today, "%Y-%m-%d")
    weekday = WEEKDAY_CN[date_obj.weekday()]
    date_text = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"

    lunch = menu.get("lunch", "") or "（未配置）"
    dinner = menu.get("dinner", "") or "（未配置）"

    return (
        f"{date_text}（{weekday}）食堂菜单\n\n"
        f"午餐：{lunch}\n"
        f"晚餐：{dinner}"
    )


def _send_feishu_text(text: str, webhook_url: str) -> None:
    payload = json.dumps(
        {
            "msg_type": "text",
            "content": {"text": f"【食堂餐品提醒】\n{text}"},
        },
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


def _resolve_feishu_webhook(feishu_cfg: dict[str, object]) -> str:
    # Priority: env var > config file
    env_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if env_url:
        return env_url

    enabled = bool(feishu_cfg.get("enabled", False))
    cfg_url = str(feishu_cfg.get("webhook_url", "")).strip()
    if enabled and cfg_url:
        return cfg_url
    return ""


def main() -> None:
    try:
        menu_by_date, feishu_cfg = _load_config()
    except Exception:
        return

    today = _today_str()
    menu = menu_by_date.get(today)
    if not menu:
        return

    content = _build_content(today, menu)

    webhook = _resolve_feishu_webhook(feishu_cfg)
    if webhook:
        try:
            _send_feishu_text(content, webhook)
        except (urllib.error.URLError, TimeoutError, ValueError):
            # Keep local popup working even if network push fails.
            pass

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo("食堂餐品提醒", content, parent=root)
    root.destroy()


if __name__ == "__main__":
    main()


