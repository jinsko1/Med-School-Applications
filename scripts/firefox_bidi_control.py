#!/usr/bin/env python3
"""Minimal Firefox WebDriver BiDi controller for a live signed-in session."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import websocket
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: websocket-client. Install it with "
        "`python3 -m pip install websocket-client`."
    ) from exc


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9222
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


class FirefoxBiDiError(RuntimeError):
    """Raised when BiDi interaction fails."""


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


def parse_evaluate_result(result: Dict[str, Any]) -> Any:
    details = result.get("result", result)
    if details.get("type") == "exception":
        raise FirefoxBiDiError(details.get("exceptionDetails", {}).get("text", "JavaScript exception"))
    if details.get("type") == "success":
        details = details.get("result", {})
    return deserialize_remote_value(details)


def deserialize_remote_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value

    kind = value.get("type")
    if kind in {"undefined", "null"}:
        return None
    if kind in {"string", "number", "boolean"}:
        return value.get("value")
    if kind == "bigint":
        return value.get("value")
    if kind == "array":
        return [deserialize_remote_value(item) for item in value.get("value", [])]
    if kind == "object":
        output: Dict[str, Any] = {}
        for item in value.get("value", []):
            key = item[0]
            if isinstance(key, dict):
                key = deserialize_remote_value(key)
            output[str(key)] = deserialize_remote_value(item[1])
        return output
    return value.get("value", value)


class BiDiSession:
    def __init__(self, host: str, port: int):
        url = f"ws://{host}:{port}/session"
        try:
            self._socket = websocket.create_connection(url, timeout=10)
        except OSError as exc:
            raise FirefoxBiDiError(
                f"Could not connect to Firefox BiDi at {url}. Launch Firefox with "
                f"`--remote-debugging-port={port}` first."
            ) from exc
        self._next_id = 0
        self.session_id = self._new_session()

    def close(self) -> None:
        try:
            self.send("session.end", {"session": self.session_id})
        except FirefoxBiDiError:
            pass
        self._socket.close()

    def _new_session(self) -> str:
        result = self.send(
            "session.new",
            {"capabilities": {"alwaysMatch": {"browserName": "firefox"}}},
            require_session=False,
        )
        return result["sessionId"]

    def send(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        require_session: bool = True,
    ) -> Dict[str, Any]:
        self._next_id += 1
        msg_id = self._next_id
        payload = {"id": msg_id, "method": method, "params": params or {}}
        if require_session:
            payload["session"] = self.session_id
        self._socket.send(json.dumps(payload))
        while True:
            message = json.loads(self._socket.recv())
            if message.get("type") == "event":
                continue
            if message.get("id") != msg_id:
                continue
            if message.get("type") == "error":
                raise FirefoxBiDiError(message.get("message") or message.get("error") or "BiDi error")
            return message.get("result", {})

    def get_tree(self) -> Dict[str, Any]:
        return self.send("browsingContext.getTree", {})

    def context_by_index(self, index: int) -> Dict[str, Any]:
        contexts = self.get_tree().get("contexts", [])
        try:
            return contexts[index]
        except IndexError as exc:
            raise FirefoxBiDiError(f"No browsing context found for index {index}.") from exc

    def evaluate(self, context_id: str, expression: str) -> Any:
        result = self.send(
            "script.evaluate",
            {
                "expression": expression,
                "target": {"context": context_id},
                "awaitPromise": True,
                "resultOwnership": "none",
            },
        )
        return parse_evaluate_result(result)

    def navigate(self, context_id: str, url: str) -> Dict[str, Any]:
        return self.send(
            "browsingContext.navigate",
            {
                "context": context_id,
                "url": url,
                "wait": "complete",
            },
        )

    def screenshot(self, context_id: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = self.send(
            "browsingContext.captureScreenshot",
            {"context": context_id},
        )
        output_path.write_bytes(base64.b64decode(result["data"]))
        return output_path


def default_output_path() -> Path:
    from time import strftime

    return Path("artifacts/browser") / f"firefox-screenshot-{strftime('%Y%m%d-%H%M%S')}.png"


def get_context(session: BiDiSession, context_id: Optional[str], context_index: int) -> Dict[str, Any]:
    if context_id:
        for context in session.get_tree().get("contexts", []):
            if context.get("context") == context_id:
                return context
        raise FirefoxBiDiError(f"No browsing context found for id {context_id}.")
    return session.context_by_index(context_index)


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=True))


def command_list(args: argparse.Namespace) -> int:
    session = BiDiSession(args.host, args.port)
    try:
        contexts = session.get_tree().get("contexts", [])
    finally:
        session.close()
    for idx, context in enumerate(contexts):
        title = context.get("title", "")
        url = context.get("url", "")
        context_id = context.get("context", "")
        print(f"[{idx}] {title}\n    url: {url}\n    context: {context_id}")
    return 0


def command_snapshot(args: argparse.Namespace) -> int:
    session = BiDiSession(args.host, args.port)
    try:
        context = get_context(session, args.context_id, args.context_index)
        snapshot = session.evaluate(
            context["context"],
            build_snapshot_js(args.limit, args.text_limit),
        )
    finally:
        session.close()
    print_json(snapshot)
    return 0


def command_navigate(args: argparse.Namespace) -> int:
    session = BiDiSession(args.host, args.port)
    try:
        context = get_context(session, args.context_id, args.context_index)
        result = session.navigate(context["context"], args.url)
    finally:
        session.close()
    print_json(result)
    return 0


def command_eval(args: argparse.Namespace) -> int:
    session = BiDiSession(args.host, args.port)
    try:
        context = get_context(session, args.context_id, args.context_index)
        result = session.evaluate(context["context"], args.expression)
    finally:
        session.close()
    print_json(result)
    return 0


def command_click(args: argparse.Namespace) -> int:
    selector = js_string(args.selector)
    expression = f"""
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
    session = BiDiSession(args.host, args.port)
    try:
        context = get_context(session, args.context_id, args.context_index)
        result = session.evaluate(context["context"], expression)
    finally:
        session.close()
    print_json(result)
    return 0


def command_type(args: argparse.Namespace) -> int:
    selector = js_string(args.selector)
    text = js_string(args.text)
    clear_first = "true" if args.clear else "false"
    submit = "true" if args.submit else "false"
    expression = f"""
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
    el.value = {text};
  }} else if (el.isContentEditable) {{
    el.innerText = {text};
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
    session = BiDiSession(args.host, args.port)
    try:
        context = get_context(session, args.context_id, args.context_index)
        result = session.evaluate(context["context"], expression)
    finally:
        session.close()
    print_json(result)
    return 0


def command_find_text(args: argparse.Namespace) -> int:
    needle = js_string(args.text.strip().lower())
    expression = f"""
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
    session = BiDiSession(args.host, args.port)
    try:
        context = get_context(session, args.context_id, args.context_index)
        result = session.evaluate(context["context"], expression)
    finally:
        session.close()
    print_json(result)
    return 0


def command_screenshot(args: argparse.Namespace) -> int:
    output = Path(args.output) if args.output else default_output_path()
    session = BiDiSession(args.host, args.port)
    try:
        context = get_context(session, args.context_id, args.context_index)
        saved = session.screenshot(context["context"], output)
    finally:
        session.close()
    print(saved)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Control a live Firefox tab through the WebDriver BiDi protocol."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)

    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text, handler in [
        ("list", "List available Firefox browsing contexts.", command_list),
        ("snapshot", "Summarize the current page.", command_snapshot),
        ("navigate", "Navigate a context to a URL.", command_navigate),
        ("click", "Click an element found by CSS selector.", command_click),
        ("type", "Type into an input or editable element.", command_type),
        ("eval", "Evaluate JavaScript in the page context.", command_eval),
        ("find-text", "Search the page text for a phrase.", command_find_text),
        ("screenshot", "Capture a PNG screenshot.", command_screenshot),
    ]:
        subparser = subparsers.add_parser(name, help=help_text)
        if name != "list":
            subparser.add_argument("--context-id")
            subparser.add_argument("--context-index", type=int, default=0)
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
        subparser.set_defaults(func=handler)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except FirefoxBiDiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
