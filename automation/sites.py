from __future__ import annotations

import datetime as dt
import importlib.util
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SiteRuntimeInput:
    name: str
    login_url: str
    username: str
    password: str
    username_selector: str
    password_selector: str
    submit_selector: str
    date_from_selector: str
    date_to_selector: str | None
    store_selector: str
    query_selector: str | None
    query_type_selector: str | None
    query_type_value: str
    file_link_selector: str | None
    download_selector: str
    flow_type: str
    query_opens_popup: bool = False
    headless: bool = True


def _fill(page, selector: str, value: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=15000)
    page.locator(selector).first.fill(value)


def _click(page, selector: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=15000)
    page.locator(selector).first.click()


def _select_option(page, selector: str, value: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=15000)
    page.locator(selector).first.select_option(label=value)


def run_single_site_download(site: SiteRuntimeInput, dates: list[dt.date], store: str, output_dir: Path) -> tuple[bool, str]:
    """基于选择器的单站点下载流程（direct_download/query_then_download/query_open_file_then_download）。"""
    if importlib.util.find_spec("playwright") is None:
        return False, "playwright not installed"

    from playwright.sync_api import sync_playwright

    date_from = dates[0].strftime("%Y-%m-%d")
    date_to = dates[-1].strftime("%Y-%m-%d")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=site.headless)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            page.goto(site.login_url, wait_until="domcontentloaded")
            _fill(page, site.username_selector, site.username)
            _fill(page, site.password_selector, site.password)
            _click(page, site.submit_selector)
            page.wait_for_timeout(1500)

            _fill(page, site.date_from_selector, date_from)
            if site.date_to_selector:
                _fill(page, site.date_to_selector, date_to)
            _fill(page, site.store_selector, store)

            if site.query_type_selector and site.query_type_value:
                _select_option(page, site.query_type_selector, site.query_type_value)

            target_page = page
            if site.flow_type in {"query_then_download", "query_open_file_then_download"}:
                if not site.query_selector:
                    return False, "missing query_selector"
                if site.query_opens_popup:
                    with context.expect_page(timeout=20000) as popup_event:
                        _click(page, site.query_selector)
                    target_page = popup_event.value
                    target_page.wait_for_load_state("domcontentloaded")
                else:
                    _click(page, site.query_selector)
                    page.wait_for_timeout(1000)

            if site.flow_type == "query_open_file_then_download":
                if not site.file_link_selector:
                    return False, "missing file_link_selector"
                _click(target_page, site.file_link_selector)
                target_page.wait_for_timeout(800)

            with target_page.expect_download(timeout=30000) as dl:
                _click(target_page, site.download_selector)
            download = dl.value
            save_path = output_dir / download.suggested_filename
            download.save_as(str(save_path))

            context.close()
            browser.close()
            return True, f"saved={save_path.name}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
