from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

import mistune
from jinja2 import Template


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "review"
SHARED_GROUPS_JSON = ROOT / "data" / "shared_essay_groups.json"
SCHOOLS_JSON = ROOT / "data" / "schools.json"
_SHARED_GROUPS: list[dict] | None = None
_SCHOOL_METADATA: dict[str, dict] | None = None

markdown = mistune.create_markdown(
    escape=False,
    plugins=["strikethrough", "table", "url"],
)


HOME_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="googlebot" content="noindex, nofollow">
  <title>Jin's Recommendation Materials</title>
  <style>
    :root {
      --bg: #f6f1e8;
      --paper: #fffdf8;
      --ink: #1e1b18;
      --muted: #655e57;
      --line: #d8cdc1;
      --accent: #355c5a;
      --accent-soft: #e3efee;
      --warm: #8b5e3c;
      --shadow: 0 18px 45px rgba(60, 42, 24, 0.08);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(139, 94, 60, 0.08), transparent 28%),
        linear-gradient(180deg, #f8f3ea 0%, #f1ebe2 100%);
      line-height: 1.65;
    }

    .shell {
      width: min(960px, calc(100vw - 32px));
      margin: 28px auto 48px;
    }

    .hero {
      background: linear-gradient(135deg, rgba(53, 92, 90, 0.96), rgba(72, 120, 110, 0.93));
      color: white;
      padding: 34px 32px 30px;
      border-radius: 20px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }

    .hero::after {
      content: "";
      position: absolute;
      right: -34px;
      bottom: -46px;
      width: 210px;
      height: 210px;
      background: rgba(255,255,255,0.14);
      -webkit-mask: url("/medicine-logo.png") center / contain no-repeat;
      mask: url("/medicine-logo.png") center / contain no-repeat;
      pointer-events: none;
    }

    h1 {
      margin: 0;
      font-size: clamp(32px, 5vw, 48px);
      line-height: 1.08;
    }

    .subtitle {
      max-width: 720px;
      margin-top: 12px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 16px;
      opacity: 0.92;
    }

    .button-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-top: 22px;
    }

    .button-card {
      display: grid;
      grid-template-columns: 54px minmax(0, 1fr);
      gap: 14px;
      align-items: center;
      min-height: 116px;
      padding: 18px;
      color: var(--ink);
      text-decoration: none;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
    }

    .button-card:hover {
      transform: translateY(-2px);
      border-color: rgba(53, 92, 90, 0.4);
      box-shadow: 0 22px 50px rgba(60, 42, 24, 0.12);
    }

    .icon-mark {
      width: 54px;
      height: 54px;
      display: grid;
      place-items: center;
      border-radius: 16px;
      color: white;
      background: var(--accent);
    }

    .icon-mark svg {
      width: 30px;
      height: 30px;
      stroke: currentColor;
      stroke-width: 1.9;
      stroke-linecap: round;
      stroke-linejoin: round;
      fill: none;
    }

    .button-title {
      display: block;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 15px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .button-detail {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 14px;
    }

    @media (max-width: 820px) {
      .button-grid { grid-template-columns: 1fr; }
      .hero { padding: 28px 24px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>Jin's Recommendation Materials</h1>
      <div class="subtitle">A small set of medical school application materials for recommendation letter writers.</div>
      <div class="subtitle">Ideal deadline: May 28</div>
    </section>
    <nav class="button-grid" aria-label="Recommendation materials">
      <a class="button-card" href="https://jinsko.com/">
        <span class="icon-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><path d="M3 12h18"></path><path d="M12 3c2.2 2.5 3.4 5.5 3.4 9s-1.2 6.5-3.4 9"></path><path d="M12 3c-2.2 2.5-3.4 5.5-3.4 9s1.2 6.5 3.4 9"></path></svg>
        </span>
        <span>
          <span class="button-title">Professional Website</span>
          <span class="button-detail">jinsko.com</span>
        </span>
      </a>
      <a class="button-card" href="/Resume/Resume.pdf">
        <span class="icon-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7z"></path><path d="M14 3v5h5"></path><path d="M9.5 13h5"></path><path d="M9.5 16h5"></path><path d="M9.5 10h2"></path></svg>
        </span>
        <span>
          <span class="button-title">Resume</span>
          <span class="button-detail">PDF</span>
        </span>
      </a>
      <a class="button-card" href="/MCAT%20Score.pdf">
        <span class="icon-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M4 19V5"></path><path d="M4 19h16"></path><path d="M8 16v-5"></path><path d="M12 16V8"></path><path d="M16 16v-7"></path><path d="M20 16v-3"></path></svg>
        </span>
        <span>
          <span class="button-title">MCAT Score</span>
          <span class="button-detail">520: 131 / 129 / 130 / 130</span>
        </span>
      </a>
      <a class="button-card" href="/essays.html">
        <span class="icon-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M4 19.5V5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-1.5z"></path><path d="M8 7h6"></path><path d="M8 11h8"></path><path d="M8 15h5"></path></svg>
        </span>
        <span>
          <span class="button-title">Essay Review Pages</span>
          <span class="button-detail">Primary and school essays</span>
        </span>
      </a>
    </nav>
  </main>
</body>
</html>
"""
)


PAGE_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="googlebot" content="noindex, nofollow">
  <title>{{ page_title }}</title>
  <style>
    :root {
      --bg: #f6f1e8;
      --paper: #fffdf8;
      --ink: #1e1b18;
      --muted: #655e57;
      --line: #d8cdc1;
      --accent: #355c5a;
      --accent-soft: #e3efee;
      --warm: #8b5e3c;
      --shadow: 0 18px 45px rgba(60, 42, 24, 0.08);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(139, 94, 60, 0.08), transparent 28%),
        linear-gradient(180deg, #f8f3ea 0%, #f1ebe2 100%);
      line-height: 1.65;
    }

    a { color: var(--accent); }
    .shell {
      width: min(1080px, calc(100vw - 32px));
      margin: 28px auto 48px;
    }

    .hero {
      background: linear-gradient(135deg, rgba(53, 92, 90, 0.96), rgba(72, 120, 110, 0.93));
      color: white;
      padding: 28px 30px 24px;
      border-radius: 20px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }

    .hero-actions {
      margin-top: 16px;
      position: relative;
      z-index: 1;
    }

    .home-button {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 9px 13px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.22);
      background: rgba(255,255,255,0.14);
      color: white;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-decoration: none;
      text-transform: uppercase;
    }

    .home-button svg {
      width: 16px;
      height: 16px;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
      fill: none;
    }

    .hero::after {
      content: "";
      position: absolute;
      inset: auto -60px -90px auto;
      width: 240px;
      height: 240px;
      background: rgba(255,255,255,0.08);
      border-radius: 50%;
    }

    .eyebrow {
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      opacity: 0.8;
      margin-bottom: 10px;
    }

    h1 {
      margin: 0 0 10px;
      font-size: clamp(28px, 4vw, 42px);
      line-height: 1.08;
    }

    .subtitle {
      max-width: 820px;
      font-size: 16px;
      opacity: 0.92;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-top: 18px;
    }

    .stat {
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.16);
      border-radius: 14px;
      padding: 12px 14px;
      backdrop-filter: blur(8px);
    }

    .stat-label {
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 11px;
      opacity: 0.8;
      margin-bottom: 5px;
    }

    .stat-value {
      font-size: 17px;
      font-weight: 700;
    }

    .content {
      margin-top: 22px;
    }

    .card, details {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }

    .card {
      padding: 24px 26px;
    }

    .card h2, details > summary {
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 14px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }

    .card h2 {
      margin: 0 0 18px;
    }

    .draft {
      font-size: 18px;
    }

    .draft h1, .draft h2, .draft h3 {
      color: var(--ink);
      margin-top: 1.35em;
    }

    .draft blockquote, .context blockquote {
      margin: 1.2em 0;
      padding: 12px 16px;
      border-left: 4px solid var(--warm);
      background: #fbf5ef;
    }

    .draft code, .context code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      background: #f2ede4;
      padding: 2px 5px;
      border-radius: 4px;
      font-size: 0.92em;
    }

    .draft pre, .context pre {
      overflow: auto;
      background: #231f1c;
      color: #f8f4ee;
      padding: 14px;
      border-radius: 10px;
    }

    details {
      padding: 0;
      overflow: hidden;
    }

    details + details, .card + details, details + .card {
      margin-top: 16px;
    }

    .context-panel {
      margin-top: 18px;
    }

    details > summary {
      list-style: none;
      cursor: pointer;
      padding: 17px 20px;
      background: linear-gradient(180deg, #fffdf9, #f5eee4);
      border-bottom: 1px solid var(--line);
    }

    details > summary::-webkit-details-marker { display: none; }
    details[open] > summary { border-bottom-color: var(--line); }
    .details-body {
      padding: 18px 20px 22px;
    }

    .context {
      font-size: 15px;
    }

    .packet-section {
      margin: 0 0 16px;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fffaf1;
    }

    .packet-section h3 {
      margin: 0 0 8px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 13px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
    }

    .packet-meta-list {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .packet-meta-list li {
      display: grid;
      grid-template-columns: minmax(120px, 180px) minmax(0, 1fr);
      gap: 10px;
      border-bottom: 1px dashed rgba(216, 205, 193, 0.8);
      padding-bottom: 8px;
    }

    .packet-meta-key {
      color: var(--muted);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 13px;
      font-weight: 700;
    }

    .note {
      margin-top: 16px;
      padding: 14px 16px;
      border-radius: 14px;
      background: var(--accent-soft);
      color: #213f3d;
      border: 1px solid rgba(53, 92, 90, 0.14);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 14px;
    }

    .index-list {
      display: grid;
      gap: 22px;
    }

    .index-group {
      overflow: hidden;
    }

    .index-group-header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 14px;
      padding: 17px 20px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      background: linear-gradient(180deg, #fffdf9, #f5eee4);
      border-bottom: 1px solid var(--line);
    }

    .index-group-header h2 {
      margin: 0;
      color: var(--ink);
      font-size: 16px;
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }

    .index-group-count {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .index-group-body {
      display: grid;
      gap: 12px;
      padding: 14px;
    }

    .index-entry {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px 18px;
      box-shadow: var(--shadow);
    }

    .index-entry h3 {
      margin: 0 0 8px;
      font-size: 22px;
    }

    .index-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 13px;
      color: var(--muted);
    }

    .chip {
      background: #f1ece4;
      border: 1px solid var(--line);
      padding: 4px 9px;
      border-radius: 999px;
    }

    @media (max-width: 900px) {
      .content { grid-template-columns: 1fr; }
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .shell { width: min(100vw - 18px, 1080px); margin-top: 14px; }
      .hero { padding: 22px 20px; border-radius: 16px; }
      .card { padding: 20px; }
    }

    @media print {
      body { background: white; }
      .shell { width: auto; margin: 0; }
      .hero, .card, details, .index-entry {
        box-shadow: none;
        border-radius: 0;
        border: 1px solid #d7d7d7;
      }
      details { break-inside: avoid; }
      .content { grid-template-columns: 1fr; }
      a { color: inherit; text-decoration: none; }
    }
  </style>
</head>
<body>
  <main class="shell">
    {% if kind == "index" %}
      <section class="hero">
        <h1>{{ page_title }}</h1>
        <div class="hero-actions">
          <a class="home-button" href="https://recs.jinsko.com/">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 11 9-8 9 8"></path><path d="M5 10v10h14V10"></path><path d="M9 20v-6h6v6"></path></svg>
            Home
          </a>
        </div>
      </section>
      <section class="index-list" style="margin-top: 20px;">
        {% for group in groups %}
          <details class="index-group"{% if group.open %} open{% endif %}>
            <summary class="index-group-header">
              <h2>{{ group.display_name }}</h2>
              <div class="index-group-count">{{ group.entries | length }} essay{% if group.entries | length != 1 %}s{% endif %}</div>
            </summary>
            <div class="index-group-body">
              {% for item in group.entries %}
                <article class="index-entry">
                  <h3><a href="{{ item.href }}">{{ item.title }}</a></h3>
                  <div class="index-meta">
                    <span class="chip">Limit: {{ item.limit or "Not listed" }}</span>
                    <span class="chip">Actual: {{ item.word_count }} words</span>
                    <span class="chip">Actual: {{ item.char_count }} characters</span>
                    <span class="chip">{{ item.relative_path }}</span>
                  </div>
                </article>
              {% endfor %}
            </div>
          </details>
        {% endfor %}
      </section>
    {% else %}
      <section class="hero">
        <div class="eyebrow">{{ eyebrow }}</div>
        <h1>{{ page_title }}</h1>
        {% if subtitle %}
        <div class="subtitle">{{ subtitle }}</div>
        {% endif %}
        <div class="grid">
          <div class="stat"><div class="stat-label">Words</div><div class="stat-value">{{ word_count }}</div></div>
          <div class="stat"><div class="stat-label">Characters</div><div class="stat-value">{{ char_count }}</div></div>
          <div class="stat"><div class="stat-label">Prompt Limit</div><div class="stat-value">{{ limit or "Not listed" }}</div></div>
          <div class="stat"><div class="stat-label">Source File</div><div class="stat-value">{{ relative_path }}</div></div>
        </div>
      </section>
      {% if reference_html %}
      <details class="context-panel">
        <summary>Reference Notes</summary>
        <div class="details-body context">{{ reference_html | safe }}</div>
      </details>
      {% endif %}
      {% if synced_source_html %}
      <details class="context-panel" open>
        <summary>Synced Draft Source</summary>
        <div class="details-body context">{{ synced_source_html | safe }}</div>
      </details>
      {% endif %}
      {% if prompt_text_html %}
      <details class="context-panel">
        <summary>Prompt</summary>
        <div class="details-body context">{{ prompt_text_html | safe }}</div>
      </details>
      {% endif %}
      {% if local_notes_html %}
      <details class="context-panel">
        <summary>Local Notes</summary>
        <div class="details-body context">{{ local_notes_html | safe }}</div>
      </details>
      {% endif %}
      {% if research_html %}
      <details class="context-panel">
        <summary>School Fit Research</summary>
        <div class="details-body context">{{ research_html | safe }}</div>
      </details>
      {% endif %}
      {% if packet_html %}
      <details class="context-panel">
        <summary>Prompt Packet Outline</summary>
        <div class="details-body context">{{ packet_html | safe }}</div>
      </details>
      {% endif %}
      <section class="content">
        <article class="card draft">
          <h2>Draft</h2>
          {{ draft_html | safe }}
        </article>
        <div class="note">
          Edit the markdown draft, then rerun <code>python3 scripts/render_review_site.py</code> to refresh this review page.
        </div>
      </section>
    {% endif %}
  </main>
</body>
</html>
"""
)


def relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def strip_markdown(text: str) -> str:
    cleaned = re.sub(r"`([^`]*)`", r"\1", text)
    cleaned = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", cleaned)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"[*_>~-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def word_count(text: str) -> int:
    stripped = strip_markdown(text)
    return len(re.findall(r"\b[\w'-]+\b", stripped))


def char_count(text: str) -> int:
    return len(strip_markdown(text))


def section_map(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "__preamble__"
    sections[current] = []
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def parse_prompt_packet(packet_text: str) -> dict[str, str]:
    sections = section_map(packet_text)
    metadata_text = sections.get("Prompt Metadata", "")
    metadata = {}
    for line in metadata_text.splitlines():
        if not line.startswith("- "):
            continue
        body = line[2:]
        if ":" in body:
            key, value = body.split(":", 1)
            metadata[key.strip()] = value.strip()
    return {
        "title": metadata.get("Title", ""),
        "limit": metadata.get("Limit", ""),
        "source": metadata.get("Source", ""),
        "prompt_text": sections.get("Prompt Text", ""),
    }


def render_packet_html(packet_text: str) -> str:
    sections = section_map(packet_text)
    parts: list[str] = []

    metadata_text = sections.get("Prompt Metadata", "")
    metadata_items = []
    for line in metadata_text.splitlines():
        if not line.startswith("- "):
            continue
        body = line[2:]
        if ":" in body:
            key, value = body.split(":", 1)
            metadata_items.append((key.strip(), value.strip()))
        elif body.strip():
            metadata_items.append(("Shared resource", body.strip()))
    if metadata_items:
        items_html = "".join(
            "<li>"
            f"<span class=\"packet-meta-key\">{html.escape(key)}</span>"
            f"<span>{html.escape(value)}</span>"
            "</li>"
            for key, value in metadata_items
        )
        parts.append(
            "<section class=\"packet-section\">"
            "<h3>Metadata</h3>"
            f"<ul class=\"packet-meta-list\">{items_html}</ul>"
            "</section>"
        )

    prompt_text = sections.get("Prompt Text", "")
    if prompt_text:
        parts.append(
            "<section class=\"packet-section\">"
            "<h3>Prompt Text</h3>"
            f"{render_md(prompt_text)}"
            "</section>"
        )

    for title, body in sections.items():
        if title in {"__preamble__", "Prompt Metadata", "Prompt Text"} or not body:
            continue
        clean_title = title
        if title == "Synced Backbone":
            clean_title = "Reusable Planning Backbone"
        parts.append(
            "<section class=\"packet-section\">"
            f"<h3>{html.escape(clean_title)}</h3>"
            f"{render_md(body)}"
            "</section>"
        )

    return "\n".join(parts)


def first_limit(text: str) -> str | None:
    match = re.search(r"\b\d[\d,]*\s+(?:characters?|words?)\b(?:\s+including\s+spaces)?", text, flags=re.I)
    if match:
        return match.group(0)
    return None


def render_md(text: str) -> str:
    return markdown(text)


def companion_context(draft_path: Path) -> dict[str, str | None]:
    result: dict[str, str | None] = {
        "school": None,
        "limit": None,
        "subtitle": "",
        "prompt_text_html": None,
        "reference_html": None,
        "local_notes_html": None,
        "research_html": None,
        "packet_html": None,
        "prompt_title": None,
        "synced_source_html": None,
        "school_slug": None,
    }

    if (
        len(draft_path.parts) >= 4
        and draft_path.parts[-4] == "schools"
        and draft_path.parent.name == "essays"
        and re.fullmatch(r"prompt-\d{2}\.draft\.md", draft_path.name)
    ):
        school_dir = draft_path.parent.parent
        result["school_slug"] = school_dir.name
        readme_path = school_dir / "README.md"
        if readme_path.exists():
            result["school"] = first_heading(readme_path.read_text(encoding="utf-8"), school_dir.name.replace("-", " "))
        else:
            result["school"] = school_dir.name.replace("-", " ")
        prefix = draft_path.name.replace(".draft.md", "")
        packet_matches = sorted(
            p
            for p in draft_path.parent.glob(f"{prefix}-*.md")
            if not p.name.endswith(".local.md") and not p.name.endswith(".draft.md")
        )
        if packet_matches:
            packet_path = packet_matches[0]
            packet_text = packet_path.read_text(encoding="utf-8")
            packet_data = parse_prompt_packet(packet_text)
            result["prompt_title"] = packet_data["title"] or None
            result["limit"] = packet_data["limit"] or None
            if packet_data["prompt_text"]:
                result["prompt_text_html"] = render_md(packet_data["prompt_text"])
            result["packet_html"] = render_packet_html(packet_text)
        local_path = draft_path.with_name(f"{prefix}.local.md")
        if local_path.exists():
            result["local_notes_html"] = render_md(local_path.read_text(encoding="utf-8"))
        research_path = school_dir / "research.md"
        if research_path.exists():
            result["research_html"] = render_md(research_path.read_text(encoding="utf-8"))
        result["subtitle"] = ""
        return result

    if draft_path.name.endswith(".draft.md"):
        companion = draft_path.with_name(draft_path.name.replace(".draft.md", ".md"))
        if companion.exists():
            companion_text = companion.read_text(encoding="utf-8")
            result["reference_html"] = render_md(companion_text)
            result["limit"] = first_limit(companion_text)
    result["subtitle"] = ""
    return result


def synced_source_html(draft_path: Path) -> str | None:
    if not draft_path.is_symlink():
        return None
    target = draft_path.resolve()
    try:
        target_label = target.relative_to(ROOT)
    except ValueError:
        target_label = target
    group = shared_group_for_target(target)
    if not group:
        return render_md(
            f"This draft is linked to `{target_label}`. Editing either file edits the same shared markdown source."
        )
    members = "\n".join(
        f"- {member['school']} - Prompt {member['prompt_index']:02d}: {member['prompt_title']}"
        for member in group.get("members", [])
    )
    return render_md(
        "\n".join(
            [
                f"Shared source: `{target_label}`",
                "",
                f"Shared group: **{group['title']}**",
                "",
                "Editing this school draft or the shared draft edits the same markdown source.",
                "",
                "Schools/prompts using this shared essay:",
                members,
            ]
        )
    )


def shared_group_for_target(target: Path) -> dict | None:
    global _SHARED_GROUPS
    if _SHARED_GROUPS is None:
        if SHARED_GROUPS_JSON.exists():
            _SHARED_GROUPS = json.loads(SHARED_GROUPS_JSON.read_text(encoding="utf-8"))
        else:
            _SHARED_GROUPS = []
    try:
        target_label = str(target.relative_to(ROOT))
    except ValueError:
        target_label = str(target)
    for group in _SHARED_GROUPS:
        if group.get("shared_draft") == target_label:
            return group
    return None


def draft_page_title(draft_path: Path, draft_text: str, context: dict[str, str | None]) -> str:
    if context.get("school") and context.get("prompt_title"):
        return f"{context['school']} - {context['prompt_title']} Draft"
    return first_heading(draft_text, draft_path.stem)


def render_draft_page(draft_path: Path) -> Path:
    draft_text = draft_path.read_text(encoding="utf-8")
    context = companion_context(draft_path)
    context["synced_source_html"] = synced_source_html(draft_path)
    title = draft_page_title(draft_path, draft_text, context)
    output_path = OUTPUT_ROOT / draft_path.relative_to(ROOT)
    output_path = output_path.with_suffix(".html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_text = PAGE_TEMPLATE.render(
        kind="page",
        page_title=title,
        eyebrow="Essay Review Page",
        subtitle=context["subtitle"],
        word_count=word_count(draft_text),
        char_count=char_count(draft_text),
        limit=context["limit"],
        relative_path=relative_to_root(draft_path),
        draft_html=render_md(draft_text),
        prompt_text_html=context["prompt_text_html"],
        reference_html=context["reference_html"],
        local_notes_html=context["local_notes_html"],
        research_html=context["research_html"],
        packet_html=context["packet_html"],
        synced_source_html=context["synced_source_html"],
    )
    output_path.write_text(html_text, encoding="utf-8")
    return output_path


def collect_drafts(targets: list[str]) -> list[Path]:
    if not targets:
        targets = ["essays/primary", "schools"]

    collected: list[Path] = []
    for raw in targets:
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT / path
        if path.is_dir():
            collected.extend(sorted(path.glob("**/*.draft.md")))
        elif path.suffix == ".md" and path.exists():
            collected.append(path)
    unique = []
    seen = set()
    for item in collected:
        key = item.absolute()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def build_index(entries: list[tuple[Path, Path]]) -> None:
    grouped_entries: dict[str, list[dict[str, object]]] = {}
    for draft_path, output_path in entries:
        draft_text = draft_path.read_text(encoding="utf-8")
        context = companion_context(draft_path)
        group_name = context["school"] or "Primary Essays"
        grouped_entries.setdefault(group_name, []).append(
            {
                "title": draft_page_title(draft_path, draft_text, context),
                "href": html.escape(str(output_path.relative_to(OUTPUT_ROOT))),
                "limit": context["limit"],
                "word_count": word_count(draft_text),
                "char_count": char_count(draft_text),
                "relative_path": relative_to_root(draft_path),
            }
        )

    groups = [
        {
            "name": name,
            "display_name": school_display_name(name),
            "entries": grouped_entries[name],
            "open": name == "Primary Essays",
        }
        for name in sorted(grouped_entries, key=lambda value: (value != "Primary Essays", value.lower()))
    ]

    index_html = PAGE_TEMPLATE.render(
        kind="index",
        page_title="Essay Review Pages",
        groups=groups,
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "essays.html").write_text(index_html, encoding="utf-8")


def school_metadata_by_name() -> dict[str, dict]:
    global _SCHOOL_METADATA
    if _SCHOOL_METADATA is None:
        if SCHOOLS_JSON.exists():
            schools = json.loads(SCHOOLS_JSON.read_text(encoding="utf-8"))
            _SCHOOL_METADATA = {school["name"]: school for school in schools}
        else:
            _SCHOOL_METADATA = {}
    return _SCHOOL_METADATA


def school_display_name(name: str) -> str:
    if name == "Primary Essays":
        return name
    school = school_metadata_by_name().get(name)
    if not school:
        return name
    percent = school.get("estimated_admit_chance_percent")
    if percent is None:
        return name
    return f"{name} - ~{percent}%"


def build_home_page() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "index.html").write_text(HOME_TEMPLATE.render(), encoding="utf-8")


def copy_public_assets() -> None:
    resume_source = ROOT / "Resume" / "Resume.pdf"
    if resume_source.exists():
        resume_output = OUTPUT_ROOT / "Resume" / "Resume.pdf"
        resume_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resume_source, resume_output)

    mcat_source = ROOT / "MCAT Score.pdf"
    if mcat_source.exists():
        shutil.copy2(mcat_source, OUTPUT_ROOT / "MCAT Score.pdf")

    medicine_logo_source = ROOT / "download-caduceus-black-medical-symbol-silhouette-png-704081694709769t2p1dqthbh.png"
    if medicine_logo_source.exists():
        shutil.copy2(medicine_logo_source, OUTPUT_ROOT / "medicine-logo.png")

    robots_text = "\n".join(
        [
            "User-agent: *",
            "Disallow: /",
            "",
        ]
    )
    (OUTPUT_ROOT / "robots.txt").write_text(robots_text, encoding="utf-8")


def clean_generated_pages() -> None:
    for relative in ("essays", "schools"):
        path = OUTPUT_ROOT / relative
        if path.exists():
            shutil.rmtree(path)
    essays_index = OUTPUT_ROOT / "essays.html"
    if essays_index.exists():
        essays_index.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render markdown essay drafts into clean review HTML pages.")
    parser.add_argument("targets", nargs="*", help="Optional markdown draft files or directories to render.")
    args = parser.parse_args()

    drafts = [path for path in collect_drafts(args.targets) if path.name.endswith(".draft.md")]
    if not drafts:
        raise SystemExit("No .draft.md files found to render.")

    if not args.targets:
        clean_generated_pages()
    rendered = [(draft, render_draft_page(draft)) for draft in drafts]
    build_index(rendered)
    build_home_page()
    copy_public_assets()
    print(f"Rendered {len(rendered)} review page(s) to {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
