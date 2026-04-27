#!/usr/bin/env python3
"""Minimal Chrome DevTools controller for a live signed-in portal session."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import websocket
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: websocket-client. Install it with "
        "`python3 -m pip install websocket-client`."
    ) from exc


DEFAULT_PORT = 9222
DEFAULT_HOST = "127.0.0.1"
INTERACTIVE_SELECTOR = ",".join(
    [
        "a[href]",
        "button",
        "input",
        "select",
        "textarea",
        "[role=button]",
        "[contenteditable='true']",
    ]
)


class BrowserControlError(RuntimeError):
    """Raised when Chrome DevTools interaction fails."""


def fetch_json(host: str, port: int, path: str) -> Any:
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise BrowserControlError(
            f"Could not reach Chrome DevTools at {url}. Launch Chrome with "
            f"`--remote-debugging-port={port}` first."
        ) from exc


def request_text(host: str, port: int, path: str) -> str:
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise BrowserControlError(f"Request failed: {url}") from exc


def list_page_targets(host: str, port: int) -> List[Dict[str, Any]]:
    targets = fetch_json(host, port, "/json/list")
    return [target for target in targets if target.get("type") == "page"]


def activate_target(host: str, port: int, target_id: str) -> None:
    request_text(host, port, f"/json/activate/{target_id}")


def default_output_path() -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return Path("artifacts/browser") / f"screenshot-{stamp}.png"


class DevToolsPage:
    def __init__(self, websocket_url: str):
        self._socket = websocket.create_connection(
            websocket_url,
            timeout=10,
            suppress_origin=True,
        )
        self._next_id = 0
        self.send("Page.enable")
        self.send("Runtime.enable")

    def close(self) -> None:
        self._socket.close()

    def send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self._next_id += 1
        msg_id = self._next_id
        payload = {"id": msg_id, "method": method, "params": params or {}}
        self._socket.send(json.dumps(payload))
        while True:
            raw_message = self._socket.recv()
            message = json.loads(raw_message)
            if message.get("id") != msg_id:
                continue
            if "error" in message:
                raise BrowserControlError(
                    f"{method} failed: {message['error'].get('message', 'unknown error')}"
                )
            return message.get("result", {})

    def evaluate(self, expression: str) -> Any:
        result = self.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        details = result.get("result", {})
        if details.get("subtype") == "error":
            raise BrowserControlError(details.get("description", "JavaScript evaluation failed"))
        return details.get("value")

    def capture_screenshot(self, output_path: Path, full_page: bool) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        params: Dict[str, Any] = {"format": "png"}
        if full_page:
            layout = self.send("Page.getLayoutMetrics")
            content_size = layout["contentSize"]
            params["clip"] = {
                "x": 0,
                "y": 0,
                "width": content_size["width"],
                "height": content_size["height"],
                "scale": 1,
            }
        data = self.send("Page.captureScreenshot", params)["data"]
        output_path.write_bytes(base64.b64decode(data))
        return output_path


def get_target(
    host: str,
    port: int,
    target_id: Optional[str],
    target_index: Optional[int],
) -> Dict[str, Any]:
    pages = list_page_targets(host, port)
    if not pages:
        raise BrowserControlError("No Chrome page targets found.")
    if target_id:
        for page in pages:
            if page.get("id") == target_id:
                return page
        raise BrowserControlError(f"No page target found for id {target_id}.")
    if target_index is not None:
        try:
            return pages[target_index]
        except IndexError as exc:
            raise BrowserControlError(f"No page target found for index {target_index}.") from exc
    if len(pages) == 1:
        return pages[0]
    formatted = "\n".join(
        f"[{idx}] {page.get('title', '(untitled)')} :: {page.get('url', '')} :: {page.get('id')}"
        for idx, page in enumerate(pages)
    )
    raise BrowserControlError(
        "Multiple tabs are open. Re-run with --target-index or --target-id.\n"
        f"{formatted}"
    )


def open_page(
    host: str,
    port: int,
    target_id: Optional[str],
    target_index: Optional[int],
) -> tuple[Dict[str, Any], DevToolsPage]:
    page = get_target(host, port, target_id, target_index)
    activate_target(host, port, page["id"])
    return page, DevToolsPage(page["webSocketDebuggerUrl"])


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=True))


def js_string(value: str) -> str:
    return json.dumps(value)


def build_snapshot_js(limit: int, text_limit: int) -> str:
    return f"""
(() => {{
  const limit = {limit};
  const textLimit = {text_limit};
  const visible = (el) => {{
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style.visibility !== "hidden" && style.display !== "none" &&
      rect.width > 0 && rect.height > 0;
  }};
  const labelFor = (el) => {{
    if (el.labels && el.labels.length) {{
      return Array.from(el.labels).map((node) => node.innerText.trim()).join(" ");
    }}
    if (el.id) {{
      const label = document.querySelector(`label[for="${{CSS.escape(el.id)}}"]`);
      if (label) return label.innerText.trim();
    }}
    return "";
  }};
  const summarize = (el, index) => {{
    const rect = el.getBoundingClientRect();
    return {{
      index,
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || el.value || "").trim().replace(/\\s+/g, " ").slice(0, 200),
      id: el.id || "",
      name: el.getAttribute("name") || "",
      type: el.getAttribute("type") || "",
      role: el.getAttribute("role") || "",
      placeholder: el.getAttribute("placeholder") || "",
      ariaLabel: el.getAttribute("aria-label") || "",
      label: labelFor(el),
      href: el.getAttribute("href") || "",
      disabled: !!el.disabled,
      rect: {{
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      }}
    }};
  }};
  const elements = Array.from(document.querySelectorAll({js_string(INTERACTIVE_SELECTOR)}))
    .filter(visible)
    .slice(0, limit)
    .map((el, index) => summarize(el, index));
  const bodyText = (document.body?.innerText || "").replace(/\\s+/g, " ").trim();
  return {{
    title: document.title,
    url: location.href,
    textPreview: bodyText.slice(0, textLimit),
    interactive: elements
  }};
}})()
"""


def command_list(args: argparse.Namespace) -> int:
    pages = list_page_targets(args.host, args.port)
    if not pages:
        print("No page targets found.")
        return 0
    for idx, page in enumerate(pages):
        title = page.get("title", "(untitled)")
        url = page.get("url", "")
        page_id = page.get("id", "")
        print(f"[{idx}] {title}\n    url: {url}\n    id: {page_id}")
    return 0


def command_snapshot(args: argparse.Namespace) -> int:
    _, session = open_page(args.host, args.port, args.target_id, args.target_index)
    try:
        snapshot = session.evaluate(build_snapshot_js(args.limit, args.text_limit))
    finally:
        session.close()
    print_json(snapshot)
    return 0


def command_navigate(args: argparse.Namespace) -> int:
    _, session = open_page(args.host, args.port, args.target_id, args.target_index)
    try:
        session.send("Page.navigate", {"url": args.url})
    finally:
        session.close()
    print(f"Navigated to {args.url}")
    return 0


def command_click(args: argparse.Namespace) -> int:
    _, session = open_page(args.host, args.port, args.target_id, args.target_index)
    selector = js_string(args.selector)
    script = f"""
(() => {{
  const el = document.querySelector({selector});
  if (!el) throw new Error("Selector not found");
  el.scrollIntoView({{block: "center", inline: "center"}});
  el.focus();
  el.click();
  return {{
    tag: el.tagName.toLowerCase(),
    text: (el.innerText || el.value || "").trim().replace(/\\s+/g, " ").slice(0, 200)
  }};
}})()
"""
    try:
        result = session.evaluate(script)
    finally:
        session.close()
    print_json(result)
    return 0


def command_type(args: argparse.Namespace) -> int:
    _, session = open_page(args.host, args.port, args.target_id, args.target_index)
    selector = js_string(args.selector)
    value = js_string(args.text)
    clear_first = "true" if args.clear else "false"
    submit = "true" if args.submit else "false"
    script = f"""
(() => {{
  const el = document.querySelector({selector});
  if (!el) throw new Error("Selector not found");
  el.scrollIntoView({{block: "center", inline: "center"}});
  el.focus();
  if ({clear_first}) {{
    if ("value" in el) el.value = "";
    if (el.isContentEditable) el.innerText = "";
  }}
  if ("value" in el) {{
    el.value = {value};
  }} else if (el.isContentEditable) {{
    el.innerText = {value};
  }} else {{
    throw new Error("Element is not writable");
  }}
  el.dispatchEvent(new Event("input", {{ bubbles: true }}));
  el.dispatchEvent(new Event("change", {{ bubbles: true }}));
  if ({submit}) {{
    const form = el.form || el.closest("form");
    if (form) {{
      if (typeof form.requestSubmit === "function") {{
        form.requestSubmit();
      }} else {{
        form.submit();
      }}
    }}
  }}
  return {{
    tag: el.tagName.toLowerCase(),
    name: el.getAttribute("name") || "",
    valueLength: ("value" in el ? el.value.length : el.innerText.length)
  }};
}})()
"""
    try:
        result = session.evaluate(script)
    finally:
        session.close()
    print_json(result)
    return 0


def command_eval(args: argparse.Namespace) -> int:
    _, session = open_page(args.host, args.port, args.target_id, args.target_index)
    try:
        result = session.evaluate(args.expression)
    finally:
        session.close()
    print_json(result)
    return 0


def command_find_text(args: argparse.Namespace) -> int:
    _, session = open_page(args.host, args.port, args.target_id, args.target_index)
    needle = js_string(args.text.strip().lower())
    script = f"""
(() => {{
  const needle = {needle};
  const bodyText = (document.body?.innerText || "").toLowerCase();
  const matches = [];
  let index = bodyText.indexOf(needle);
  while (index !== -1 && matches.length < 20) {{
    const start = Math.max(0, index - 80);
    const end = Math.min(bodyText.length, index + needle.length + 80);
    matches.push(bodyText.slice(start, end).replace(/\\s+/g, " ").trim());
    index = bodyText.indexOf(needle, index + needle.length);
  }}
  return {{
    found: matches.length > 0,
    count: matches.length,
    excerpts: matches
  }};
}})()
"""
    try:
        result = session.evaluate(script)
    finally:
        session.close()
    print_json(result)
    return 0


def command_screenshot(args: argparse.Namespace) -> int:
    _, session = open_page(args.host, args.port, args.target_id, args.target_index)
    output = Path(args.output) if args.output else default_output_path()
    try:
        saved = session.capture_screenshot(output, full_page=args.full_page)
    finally:
        session.close()
    print(saved)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Control a live Chrome tab through the DevTools protocol."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available Chrome page targets.")
    list_parser.set_defaults(func=command_list)

    for name, help_text, handler in [
        ("snapshot", "Summarize the current page.", command_snapshot),
        ("navigate", "Navigate the target tab to a URL.", command_navigate),
        ("click", "Click an element found by CSS selector.", command_click),
        ("type", "Type into an input or editable element.", command_type),
        ("eval", "Evaluate JavaScript in the page context.", command_eval),
        ("find-text", "Search the page text for a phrase.", command_find_text),
        ("screenshot", "Capture a PNG screenshot.", command_screenshot),
    ]:
        subparser = subparsers.add_parser(name, help=help_text)
        subparser.add_argument("--target-id")
        subparser.add_argument("--target-index", type=int)
        if name == "snapshot":
            subparser.add_argument("--limit", type=int, default=25)
            subparser.add_argument("--text-limit", type=int, default=1200)
        elif name == "navigate":
            subparser.add_argument("--url", required=True)
        elif name == "click":
            subparser.add_argument("--selector", required=True)
        elif name == "type":
            subparser.add_argument("--selector", required=True)
            subparser.add_argument("--text", required=True)
            subparser.add_argument("--clear", action="store_true")
            subparser.add_argument("--submit", action="store_true")
        elif name == "eval":
            subparser.add_argument("--expression", required=True)
        elif name == "find-text":
            subparser.add_argument("--text", required=True)
        elif name == "screenshot":
            subparser.add_argument("--output")
            subparser.add_argument("--full-page", action="store_true")
        subparser.set_defaults(func=handler)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except BrowserControlError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
