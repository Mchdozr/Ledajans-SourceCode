#!/usr/bin/env python3
"""Chrome CSS coverage ile mobil anasayfa kritik tema kurallarını çıkar."""
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import AGENT_HUB, ROOT

CHROME_PATH = "/usr/local/bin/google-chrome"
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 11; moto g power (2022)) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36"
)
DEFAULT_INCLUDES = ["bootstrap.css", "template.css"]


class CdpClient:
    def __init__(self, url: str):
        self.ws = websocket.create_connection(url, timeout=10)
        self.next_id = 1
        self.stylesheets: dict[str, dict] = {}

    def _remember_event(self, message: dict) -> None:
        if message.get("method") == "CSS.styleSheetAdded":
            header = message.get("params", {}).get("header", {})
            stylesheet_id = header.get("styleSheetId")
            if stylesheet_id:
                self.stylesheets[stylesheet_id] = header

    def call(self, method: str, params: dict | None = None) -> dict:
        call_id = self.next_id
        self.next_id += 1
        self.ws.send(json.dumps({"id": call_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            self._remember_event(message)
            if message.get("id") != call_id:
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message.get("result", {})

    def wait_for_event(self, method: str, timeout: float = 30) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = json.loads(self.ws.recv())
            self._remember_event(message)
            if message.get("method") == method:
                return message.get("params", {})
        raise TimeoutError(method)

    def drain(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        self.ws.settimeout(0.2)
        try:
            while time.monotonic() < deadline:
                try:
                    message = json.loads(self.ws.recv())
                except (TimeoutError, websocket.WebSocketTimeoutException):
                    continue
                self._remember_event(message)
        finally:
            self.ws.settimeout(10)

    def close(self) -> None:
        self.ws.close()


def available_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_page(port: int, timeout: float = 20) -> str:
    deadline = time.monotonic() + timeout
    endpoint = f"http://127.0.0.1:{port}/json"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(endpoint, timeout=2) as response:
                pages = json.load(response)
            page = next((item for item in pages if item.get("type") == "page"), None)
            if page and page.get("webSocketDebuggerUrl"):
                return str(page["webSocketDebuggerUrl"])
        except (OSError, ValueError):
            time.sleep(0.2)
    raise TimeoutError("Chrome CDP page bulunamadı")


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def collect(url: str, includes: list[str]) -> list[dict]:
    port = available_port()
    with tempfile.TemporaryDirectory(prefix="ledajans-css-coverage-") as profile:
        chrome = subprocess.Popen(
            [
                CHROME_PATH,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--remote-allow-origins=*",
                f"--remote-debugging-port={port}",
                f"--user-data-dir={profile}",
                "about:blank",
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        client: CdpClient | None = None
        try:
            client = CdpClient(wait_for_page(port))
            client.call("Page.enable")
            client.call("Network.enable")
            client.call("DOM.enable")
            client.call("CSS.enable")
            client.call(
                "Network.setUserAgentOverride",
                {"userAgent": MOBILE_USER_AGENT, "platform": "Android"},
            )
            client.call(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 412,
                    "height": 823,
                    "deviceScaleFactor": 1.75,
                    "mobile": True,
                },
            )
            client.call("CSS.startRuleUsageTracking")
            client.call("Page.navigate", {"url": url})
            client.wait_for_event("Page.loadEventFired", timeout=60)
            client.drain(2)
            usage = client.call("CSS.stopRuleUsageTracking").get("ruleUsage", [])

            by_stylesheet: dict[str, list[tuple[int, int]]] = {}
            for item in usage:
                if not item.get("used"):
                    continue
                stylesheet_id = str(item.get("styleSheetId", ""))
                header = client.stylesheets.get(stylesheet_id, {})
                source_url = str(header.get("sourceURL", ""))
                if not any(needle in source_url for needle in includes):
                    continue
                by_stylesheet.setdefault(stylesheet_id, []).append(
                    (int(item["startOffset"]), int(item["endOffset"]))
                )

            reports: list[dict] = []
            for stylesheet_id, ranges in by_stylesheet.items():
                header = client.stylesheets[stylesheet_id]
                text = client.call(
                    "CSS.getStyleSheetText",
                    {"styleSheetId": stylesheet_id},
                ).get("text", "")
                merged = merge_ranges(ranges)
                reports.append(
                    {
                        "url": header.get("sourceURL", ""),
                        "total_chars": len(text),
                        "used_chars": sum(end - start for start, end in merged),
                        "ranges": [
                            {
                                "start": start,
                                "end": end,
                                "css": text[start:end],
                            }
                            for start, end in merged
                        ],
                    }
                )
            return reports
        finally:
            if client:
                client.close()
            chrome.terminate()
            try:
                chrome.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome.kill()
                chrome.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://ledajans.com/")
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument(
        "--output",
        type=Path,
        default=AGENT_HUB / "REPORTS" / "mobile-critical-css-coverage.json",
    )
    args = parser.parse_args()
    includes = args.include or DEFAULT_INCLUDES
    reports = collect(args.url, includes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"url": args.url, "stylesheets": reports}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    for report in reports:
        ratio = (report["used_chars"] / report["total_chars"] * 100) if report["total_chars"] else 0
        print(
            f"{report['url']}: {report['used_chars']}/{report['total_chars']} "
            f"karakter ({ratio:.1f}%)"
        )
    print(f"OK: {args.output}")
    return 0 if reports else 1


if __name__ == "__main__":
    raise SystemExit(main())
