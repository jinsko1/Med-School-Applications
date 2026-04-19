from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import mistune
from jinja2 import Template


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "review"

markdown = mistune.create_markdown(
    escape=False,
    plugins=["strikethrough", "table", "url"],
)


PAGE_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
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
      grid-template-columns: repeat(4, minmax(0, 1fr));
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
      display: grid;
      grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.95fr);
      gap: 22px;
      margin-top: 22px;
      align-items: start;
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
      gap: 14px;
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
        <div class="eyebrow">Markdown Review Index</div>
        <h1>{{ page_title }}</h1>
        <div class="subtitle">{{ subtitle }}</div>
      </section>
      <section class="index-list" style="margin-top: 20px;">
        {% for item in entries %}
          <article class="index-entry">
            <h3><a href="{{ item.href }}">{{ item.title }}</a></h3>
            <div class="index-meta">
              {% if item.school %}<span class="chip">{{ item.school }}</span>{% endif %}
              {% if item.limit %}<span class="chip">{{ item.limit }}</span>{% endif %}
              <span class="chip">{{ item.word_count }} words</span>
              <span class="chip">{{ item.relative_path }}</span>
            </div>
          </article>
        {% endfor %}
      </section>
    {% else %}
      <section class="hero">
        <div class="eyebrow">{{ eyebrow }}</div>
        <h1>{{ page_title }}</h1>
        <div class="subtitle">{{ subtitle }}</div>
        <div class="grid">
          <div class="stat"><div class="stat-label">Words</div><div class="stat-value">{{ word_count }}</div></div>
          <div class="stat"><div class="stat-label">Characters</div><div class="stat-value">{{ char_count }}</div></div>
          <div class="stat"><div class="stat-label">Prompt Limit</div><div class="stat-value">{{ limit or "Not listed" }}</div></div>
          <div class="stat"><div class="stat-label">Source File</div><div class="stat-value">{{ relative_path }}</div></div>
        </div>
      </section>
      <section class="content">
        <div>
          <article class="card draft">
            <h2>Draft</h2>
            {{ draft_html | safe }}
          </article>
          {% if prompt_text_html %}
          <article class="card context" style="margin-top: 16px;">
            <h2>Prompt</h2>
            {{ prompt_text_html | safe }}
          </article>
          {% endif %}
        </div>
        <aside>
          {% if reference_html %}
          <details open>
            <summary>Reference Notes</summary>
            <div class="details-body context">{{ reference_html | safe }}</div>
          </details>
          {% endif %}
          {% if local_notes_html %}
          <details open>
            <summary>Local Notes</summary>
            <div class="details-body context">{{ local_notes_html | safe }}</div>
          </details>
          {% endif %}
          {% if research_html %}
          <details>
            <summary>School Research</summary>
            <div class="details-body context">{{ research_html | safe }}</div>
          </details>
          {% endif %}
          {% if packet_html %}
          <details>
            <summary>Full Prompt Packet</summary>
            <div class="details-body context">{{ packet_html | safe }}</div>
          </details>
          {% endif %}
          <div class="note">
            Edit the markdown draft, then rerun <code>python3 scripts/render_review_site.py</code> to refresh this review page.
          </div>
        </aside>
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
    }

    if (
        len(draft_path.parts) >= 4
        and draft_path.parts[-4] == "schools"
        and draft_path.parent.name == "essays"
        and re.fullmatch(r"prompt-\d{2}\.draft\.md", draft_path.name)
    ):
        school_dir = draft_path.parent.parent
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
            result["limit"] = packet_data["limit"] or None
            if packet_data["prompt_text"]:
                result["prompt_text_html"] = render_md(packet_data["prompt_text"])
            result["packet_html"] = render_md(packet_text)
        local_path = draft_path.with_name(f"{prefix}.local.md")
        if local_path.exists():
            result["local_notes_html"] = render_md(local_path.read_text(encoding="utf-8"))
        research_path = school_dir / "research.md"
        if research_path.exists():
            result["research_html"] = render_md(research_path.read_text(encoding="utf-8"))
        result["subtitle"] = "Draft for reviewer-friendly sharing with prompt and school context attached."
        return result

    if draft_path.name.endswith(".draft.md"):
        companion = draft_path.with_name(draft_path.name.replace(".draft.md", ".md"))
        if companion.exists():
            result["reference_html"] = render_md(companion.read_text(encoding="utf-8"))
    result["subtitle"] = "Markdown draft rendered in a cleaner format for review and print."
    return result


def render_draft_page(draft_path: Path) -> Path:
    draft_text = draft_path.read_text(encoding="utf-8")
    title = first_heading(draft_text, draft_path.stem)
    context = companion_context(draft_path)
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
    )
    output_path.write_text(html_text, encoding="utf-8")
    return output_path


def collect_drafts(targets: list[str]) -> list[Path]:
    if not targets:
        return sorted(ROOT.glob("**/*.draft.md"))

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
        resolved = item.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(item)
    return unique


def build_index(entries: list[tuple[Path, Path]]) -> None:
    index_entries = []
    for draft_path, output_path in entries:
        draft_text = draft_path.read_text(encoding="utf-8")
        context = companion_context(draft_path)
        index_entries.append(
            {
                "title": first_heading(draft_text, draft_path.stem),
                "href": html.escape(str(output_path.relative_to(OUTPUT_ROOT))),
                "school": context["school"],
                "limit": context["limit"],
                "word_count": word_count(draft_text),
                "relative_path": relative_to_root(draft_path),
            }
        )

    index_html = PAGE_TEMPLATE.render(
        kind="index",
        page_title="Essay Review Pages",
        subtitle="Write in markdown, then use these polished HTML pages for mentor review, browser reading, or print-to-PDF.",
        entries=index_entries,
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "index.html").write_text(index_html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render markdown essay drafts into clean review HTML pages.")
    parser.add_argument("targets", nargs="*", help="Optional markdown draft files or directories to render.")
    args = parser.parse_args()

    drafts = [path for path in collect_drafts(args.targets) if path.name.endswith(".draft.md")]
    if not drafts:
        raise SystemExit("No .draft.md files found to render.")

    rendered = [(draft, render_draft_page(draft)) for draft in drafts]
    build_index(rendered)
    print(f"Rendered {len(rendered)} review page(s) to {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
