from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
from functools import lru_cache
from pathlib import Path

import mistune
from jinja2 import Template


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "review"
SHARED_GROUPS_JSON = ROOT / "data" / "shared_essay_groups.json"
SCHOOLS_JSON = ROOT / "data" / "schools.json"
SCHOOL_PAPERS_JSON = ROOT / "data" / "school_research_papers.json"
SCHOOL_MAJOR_CONTRIBUTIONS_JSON = ROOT / "data" / "school_major_contributions.json"
SECONDARY_PORTALS_JSON = ROOT / "data" / "secondary_portals.json"
SCHOOL_COMPLETION_STATUS_JSON = ROOT / "data" / "school_completion_status.json"
_SHARED_GROUPS: list[dict] | None = None
_SCHOOL_METADATA: dict[str, dict] | None = None
_SCHOOL_PAPERS: dict[str, list[dict]] | None = None
_SCHOOL_MAJOR_CONTRIBUTIONS: dict[str, dict] | None = None
_SECONDARY_PORTALS: dict[str, dict] | None = None
_SCHOOL_COMPLETION_STATUS: dict[str, dict] | None = None

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
  <link rel="icon" type="image/png" href="favicon.png">
  <link rel="shortcut icon" type="image/png" href="favicon.png">
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
  <link rel="icon" type="image/png" href="{{ favicon_href }}">
  <link rel="shortcut icon" type="image/png" href="{{ favicon_href }}">
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

    .school-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-top: 20px;
    }

    .progress-card {
      margin-top: 20px;
      padding: 18px 20px;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }

    .progress-topline {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 14px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .progress-title {
      color: var(--ink);
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .progress-count {
      color: #145a31;
      font-size: 18px;
      font-weight: 800;
      white-space: nowrap;
    }

    .progress-track {
      height: 13px;
      margin-top: 12px;
      overflow: hidden;
      background: #efe7dc;
      border: 1px solid rgba(216, 205, 193, 0.9);
      border-radius: 999px;
    }

    .progress-fill {
      width: var(--progress-percent);
      height: 100%;
      background: linear-gradient(90deg, #2f7d52, #7fb069);
      border-radius: inherit;
      box-shadow: 0 8px 18px rgba(47, 125, 82, 0.18);
    }

    .progress-note {
      margin: 9px 0 0;
      color: var(--muted);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 13px;
    }

    .school-card {
      display: grid;
      gap: 12px;
      min-height: 172px;
      padding: 20px;
      color: var(--ink);
      text-decoration: none;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      position: relative;
      transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
    }

    .school-card.is-complete {
      border-color: rgba(47, 125, 82, 0.34);
    }

    .school-card.is-complete h2 {
      padding-right: 112px;
    }

    .completion-badge {
      position: absolute;
      top: 14px;
      right: 14px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 9px;
      color: #145a31;
      background: #e5f5eb;
      border: 1px solid rgba(47, 125, 82, 0.25);
      border-radius: 999px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.04em;
      line-height: 1;
      text-transform: uppercase;
      box-shadow: 0 8px 18px rgba(47, 125, 82, 0.12);
    }

    .completion-badge svg {
      width: 14px;
      height: 14px;
      stroke: currentColor;
      stroke-width: 2.5;
      stroke-linecap: round;
      stroke-linejoin: round;
      fill: none;
    }

    .completion-badge-hero {
      color: white;
      background: rgba(25, 128, 74, 0.84);
      border-color: rgba(255,255,255,0.2);
      z-index: 2;
    }

    .school-card:hover {
      transform: translateY(-2px);
      border-color: rgba(53, 92, 90, 0.42);
      box-shadow: 0 22px 50px rgba(60, 42, 24, 0.12);
    }

    .school-card h2 {
      margin: 0;
      font-size: 22px;
      line-height: 1.2;
    }

    .school-card-meta,
    .school-card-fact {
      margin: 0;
      color: var(--muted);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 13px;
      line-height: 1.45;
    }

    .school-card-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .section-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 18px;
      margin-top: 20px;
    }

    .essay-grid,
    .paper-grid {
      display: grid;
      gap: 12px;
    }

    .essay-button,
    .paper-card {
      display: block;
      padding: 16px 18px;
      color: var(--ink);
      text-decoration: none;
      background: #fffaf1;
      border: 1px solid var(--line);
      border-radius: 16px;
    }

    .essay-button h3,
    .paper-card h3 {
      margin: 0 0 8px;
      font-size: 20px;
      line-height: 1.25;
    }

    .paper-card p {
      margin: 8px 0 0;
    }

    .meta-table {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .meta-table li {
      display: grid;
      grid-template-columns: minmax(150px, 230px) minmax(0, 1fr);
      gap: 12px;
      padding-bottom: 8px;
      border-bottom: 1px dashed rgba(216, 205, 193, 0.8);
    }

    .meta-key {
      color: var(--muted);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
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
      .school-grid { grid-template-columns: 1fr; }
      .progress-topline { align-items: flex-start; flex-direction: column; gap: 4px; }
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
        <div class="subtitle">Start with a school, then click into only the essays and context you need.</div>
        <div class="hero-actions">
          <a class="home-button" href="https://recs.jinsko.com/">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 11 9-8 9 8"></path><path d="M5 10v10h14V10"></path><path d="M9 20v-6h6v6"></path></svg>
            Home
          </a>
        </div>
      </section>
      {% if progress %}
      <section class="progress-card" aria-label="Secondary essay completion progress">
        <div class="progress-topline">
          <div class="progress-title">Secondary Progress</div>
          <div class="progress-count">{{ progress.completed }} / {{ progress.total }} schools</div>
        </div>
        <div class="progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="{{ progress.total }}" aria-valuenow="{{ progress.completed }}" aria-label="{{ progress.completed }} of {{ progress.total }} schools complete">
          <div class="progress-fill" style="--progress-percent: {{ progress.percent }}%;"></div>
        </div>
        <p class="progress-note">{{ progress.remaining }} school{% if progress.remaining != 1 %}s{% endif %} remaining.</p>
      </section>
      {% endif %}
      {% if primary_entries %}
      <section class="index-list" style="margin-top: 20px;">
        <details class="index-group" open>
          <summary class="index-group-header">
            <h2>Primary Essays</h2>
            <div class="index-group-count">{{ primary_entries | length }} essay{% if primary_entries | length != 1 %}s{% endif %}</div>
          </summary>
          <div class="index-group-body">
            {% for item in primary_entries %}
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
      </section>
      {% endif %}
      <section class="school-grid" aria-label="School essay dashboards">
        {% for school in schools %}
        <a class="school-card{% if school.completion_status %} is-complete{% endif %}" href="{{ school.href }}">
          {% if school.completion_status %}
          <span class="completion-badge" aria-label="Secondary essays complete">
            <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.2 8.4 6.5 11.6 12.8 4.4"></path></svg>
            Done
          </span>
          {% endif %}
          <h2>{{ school.display_name }}</h2>
          <p class="school-card-meta">
            <span class="chip">{{ school.location or "Location not listed" }}</span>
            <span class="chip">GPA {{ school.median_gpa or "N/A" }}</span>
            <span class="chip">MCAT {{ school.median_mcat or "N/A" }}</span>
            <span class="chip">{{ school.essay_count }} essays</span>
            {% if school.secondary_portal %}<span class="chip">Portal live</span>{% endif %}
          </p>
          <p class="school-card-fact">{{ school.why_school_fact }}</p>
        </a>
        {% endfor %}
      </section>
    {% elif kind == "school" %}
      <section class="hero">
        {% if completion_status %}
        <div class="completion-badge completion-badge-hero" aria-label="Secondary essays complete">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.2 8.4 6.5 11.6 12.8 4.4"></path></svg>
          Complete
        </div>
        {% endif %}
        <div class="eyebrow">School Dashboard</div>
        <h1>{{ page_title }}</h1>
        <div class="subtitle">{{ school.why_school_fact }}</div>
        <div class="grid">
          <div class="stat"><div class="stat-label">Estimate</div><div class="stat-value">~{{ school.estimated_admit_chance_percent }}%</div></div>
          <div class="stat"><div class="stat-label">GPA Median</div><div class="stat-value">{{ school.median_gpa or "N/A" }}</div></div>
          <div class="stat"><div class="stat-label">MCAT Median</div><div class="stat-value">{{ school.median_mcat or "N/A" }}</div></div>
          <div class="stat"><div class="stat-label">Essays</div><div class="stat-value">{{ entries | length }}</div></div>
        </div>
        <div class="hero-actions">
          <a class="home-button" href="../../essays.html">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"></path></svg>
            All Schools
          </a>
          {% if secondary_portal %}
          <a class="home-button" href="{{ secondary_portal.url }}">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7"></path><path d="M8 7h9v9"></path></svg>
            Secondary Portal
          </a>
          {% endif %}
        </div>
      </section>
      <section class="section-grid">
        <article class="card">
          <h2>School Details</h2>
          <ul class="meta-table">
            <li><span class="meta-key">Location</span><span>{{ school.location or "Not listed" }}</span></li>
            <li><span class="meta-key">COA / Year</span><span>{{ school.coa_per_year or "Not listed" }}</span></li>
            <li><span class="meta-key">Secondary Cycle</span><span>{{ school.secondary_cycle or "Not listed" }}</span></li>
            <li><span class="meta-key">Deadline</span><span>{{ school.secondary_deadline or "See admissions source" }}</span></li>
            {% if secondary_portal %}
            <li><span class="meta-key">Secondary Portal</span><span><a href="{{ secondary_portal.url }}">{{ secondary_portal.label }}</a></span></li>
            {% endif %}
            <li><span class="meta-key">Official Page</span><span><a href="{{ school.official_url }}">{{ school.official_url }}</a></span></li>
            <li><span class="meta-key">Prompt Source</span><span><a href="{{ school.prompt_source }}">{{ school.prompt_source }}</a></span></li>
            <li><span class="meta-key">List Note</span><span>{{ school.notes }}</span></li>
          </ul>
        </article>
        {% if major_contribution %}
        <article class="card">
          <h2>Major Contribution to Science</h2>
          <h3><a href="{{ major_contribution.source_url }}">{{ major_contribution.title }}</a></h3>
          <p>{{ major_contribution.contribution }}</p>
          {% if major_contribution.writer_note %}
          <p class="note">{{ major_contribution.writer_note }}</p>
          {% endif %}
          <div class="index-meta">
            <span class="chip">{{ major_contribution.source_label or "Source" }}</span>
          </div>
        </article>
        {% endif %}
        <article class="card">
          <h2>Recent / Relevant Research</h2>
          <p class="note">Curated from PubMed-affiliated results for major work, microbiology/infectious-disease relevance, women's health, underserved care, or hospice/palliative fit. Schools are left blank when the available matches look too weak to cite confidently.</p>
          {% if papers %}
          <div class="paper-grid">
            {% for paper in papers %}
            <article class="paper-card">
              <h3><a href="{{ paper.url }}">{{ paper.title }}</a></h3>
              <div class="index-meta">
                <span class="chip">{{ paper.year or "Year not listed" }}</span>
                <span class="chip">{{ paper.journal or "Journal not listed" }}</span>
                {% if paper.pmid %}<span class="chip">PMID {{ paper.pmid }}</span>{% endif %}
              </div>
              <p>{{ paper.synopsis }}</p>
            </article>
            {% endfor %}
          </div>
          {% else %}
          <p>No publication synopsis has been added yet for this school.</p>
          {% endif %}
        </article>
        <article class="card">
          <h2>Essays</h2>
          <div class="essay-grid">
            {% for item in entries %}
            <a class="essay-button" href="{{ item.href }}">
              <h3>{{ item.prompt_title or item.title }}</h3>
              <div class="index-meta">
                <span class="chip">Limit: {{ item.limit or "Not listed" }}</span>
                <span class="chip">Actual: {{ item.word_count }} words</span>
                <span class="chip">Actual: {{ item.char_count }} characters</span>
                {% if item.shared_group %}<span class="chip">Shared: {{ item.shared_group }}</span>{% endif %}
              </div>
              {% if item.prompt_text_excerpt %}<p>{{ item.prompt_text_excerpt }}</p>{% endif %}
            </a>
            {% endfor %}
          </div>
        </article>
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


def favicon_href_for_output(output_path: Path) -> str:
    return Path(os.path.relpath(OUTPUT_ROOT / "favicon.png", output_path.parent)).as_posix()


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


@lru_cache(maxsize=None)
def cached_read_text(path_label: str) -> str:
    return Path(path_label).read_text(encoding="utf-8")


def read_text(path: Path) -> str:
    return cached_read_text(str(path))


@lru_cache(maxsize=None)
def render_md(text: str) -> str:
    return markdown(text)


def companion_context(draft_path: Path) -> dict[str, str | None]:
    result: dict[str, str | None] = {
        "school": None,
        "limit": None,
        "subtitle": "",
        "prompt_text_html": None,
        "prompt_text_raw": None,
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
            result["school"] = first_heading(read_text(readme_path), school_dir.name.replace("-", " "))
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
            packet_text = read_text(packet_path)
            packet_data = parse_prompt_packet(packet_text)
            result["prompt_title"] = packet_data["title"] or None
            result["limit"] = packet_data["limit"] or None
            if packet_data["prompt_text"]:
                result["prompt_text_raw"] = packet_data["prompt_text"]
                result["prompt_text_html"] = render_md(packet_data["prompt_text"])
            result["packet_html"] = render_packet_html(packet_text)
        local_path = draft_path.with_name(f"{prefix}.local.md")
        if local_path.exists():
            result["local_notes_html"] = render_md(read_text(local_path))
        research_path = school_dir / "research.md"
        if research_path.exists():
            result["research_html"] = render_md(read_text(research_path))
        result["subtitle"] = ""
        return result

    if draft_path.name.endswith(".draft.md"):
        companion = draft_path.with_name(draft_path.name.replace(".draft.md", ".md"))
        if companion.exists():
            companion_text = read_text(companion)
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


def output_path_for_draft(draft_path: Path) -> Path:
    return (OUTPUT_ROOT / draft_path.relative_to(ROOT)).with_suffix(".html")


def render_draft_page(draft_path: Path) -> Path:
    draft_text = read_text(draft_path)
    context = companion_context(draft_path)
    context["synced_source_html"] = synced_source_html(draft_path)
    title = draft_page_title(draft_path, draft_text, context)
    output_path = output_path_for_draft(draft_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_text = PAGE_TEMPLATE.render(
        kind="page",
        page_title=title,
        favicon_href=favicon_href_for_output(output_path),
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
            if path.name.endswith(".draft.md"):
                collected.append(path)
            else:
                prompt_match = re.match(r"(prompt-\d{2})", path.name)
                draft = path.with_name(f"{prompt_match.group(1)}.draft.md") if prompt_match else None
                if draft and draft.exists():
                    collected.append(draft)
    unique = []
    seen = set()
    for item in collected:
        key = item.absolute()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def school_slugs_for_drafts(drafts: list[Path]) -> set[str]:
    slugs: set[str] = set()
    for draft_path in drafts:
        if (
            len(draft_path.parts) >= 4
            and draft_path.parts[-4] == "schools"
            and draft_path.parent.name == "essays"
        ):
            slugs.add(draft_path.parent.parent.name)
    return slugs


def entry_for_draft(draft_path: Path) -> tuple[dict[str, object], str | None]:
    draft_text = read_text(draft_path)
    context = companion_context(draft_path)
    output_path = output_path_for_draft(draft_path)
    entry = {
        "title": draft_page_title(draft_path, draft_text, context),
        "prompt_title": context.get("prompt_title"),
        "href": html.escape(str(output_path.relative_to(OUTPUT_ROOT))),
        "limit": context["limit"],
        "word_count": word_count(draft_text),
        "char_count": char_count(draft_text),
        "relative_path": relative_to_root(draft_path),
        "prompt_text_excerpt": prompt_excerpt(context.get("prompt_text_raw")),
        "shared_group": shared_group_title_for_draft(draft_path),
    }
    return entry, context.get("school_slug")


def build_index(drafts: list[Path], school_page_slugs: set[str] | None = None) -> None:
    grouped_entries: dict[str, list[dict[str, object]]] = {}
    school_entries: dict[str, list[dict[str, object]]] = {}
    primary_entries: list[dict[str, object]] = []
    secondary_portals = secondary_portals_by_slug()
    completion_statuses = school_completion_status_by_slug()
    for draft_path in drafts:
        context = companion_context(draft_path)
        group_name = context["school"] or "Primary Essays"
        entry, school_slug = entry_for_draft(draft_path)
        grouped_entries.setdefault(group_name, []).append(entry)
        if school_slug:
            school_entries.setdefault(str(school_slug), []).append(entry)
        else:
            primary_entries.append(entry)

    build_school_pages(school_entries, only_slugs=school_page_slugs)

    schools = []
    for school in all_school_metadata():
        slug = school["slug"]
        entries_for_school = school_entries.get(slug, [])
        if not entries_for_school:
            continue
        schools.append(
            {
                **school,
                "display_name": school_display_name(school["name"]),
                "href": html.escape(f"schools/{slug}/index.html"),
                "essay_count": len(entries_for_school),
                "secondary_portal": secondary_portals.get(slug),
                "completion_status": completion_statuses.get(slug),
            }
        )
    schools.sort(key=lambda school: school["name"].lower())
    completed_count = sum(1 for school in schools if school.get("completion_status"))
    total_count = len(schools)
    progress = {
        "completed": completed_count,
        "total": total_count,
        "remaining": max(total_count - completed_count, 0),
        "percent": round((completed_count / total_count) * 100, 1) if total_count else 0,
    }

    index_html = PAGE_TEMPLATE.render(
        kind="index",
        page_title="Essay Review Pages",
        favicon_href="favicon.png",
        primary_entries=primary_entries,
        schools=schools,
        progress=progress,
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


def all_school_metadata() -> list[dict]:
    if not SCHOOLS_JSON.exists():
        return []
    return json.loads(SCHOOLS_JSON.read_text(encoding="utf-8"))


def school_metadata_by_slug() -> dict[str, dict]:
    return {school["slug"]: school for school in all_school_metadata()}


def school_papers_by_slug() -> dict[str, list[dict]]:
    global _SCHOOL_PAPERS
    if _SCHOOL_PAPERS is None:
        if SCHOOL_PAPERS_JSON.exists():
            _SCHOOL_PAPERS = json.loads(SCHOOL_PAPERS_JSON.read_text(encoding="utf-8"))
        else:
            _SCHOOL_PAPERS = {}
    return _SCHOOL_PAPERS


def school_major_contributions_by_slug() -> dict[str, dict]:
    global _SCHOOL_MAJOR_CONTRIBUTIONS
    if _SCHOOL_MAJOR_CONTRIBUTIONS is None:
        if SCHOOL_MAJOR_CONTRIBUTIONS_JSON.exists():
            _SCHOOL_MAJOR_CONTRIBUTIONS = json.loads(
                SCHOOL_MAJOR_CONTRIBUTIONS_JSON.read_text(encoding="utf-8")
            )
        else:
            _SCHOOL_MAJOR_CONTRIBUTIONS = {}
    return _SCHOOL_MAJOR_CONTRIBUTIONS


def secondary_portals_by_slug() -> dict[str, dict]:
    global _SECONDARY_PORTALS
    if _SECONDARY_PORTALS is None:
        if SECONDARY_PORTALS_JSON.exists():
            _SECONDARY_PORTALS = json.loads(SECONDARY_PORTALS_JSON.read_text(encoding="utf-8"))
        else:
            _SECONDARY_PORTALS = {}
    return _SECONDARY_PORTALS


def school_completion_status_by_slug() -> dict[str, dict]:
    global _SCHOOL_COMPLETION_STATUS
    if _SCHOOL_COMPLETION_STATUS is None:
        if SCHOOL_COMPLETION_STATUS_JSON.exists():
            _SCHOOL_COMPLETION_STATUS = json.loads(SCHOOL_COMPLETION_STATUS_JSON.read_text(encoding="utf-8"))
        else:
            _SCHOOL_COMPLETION_STATUS = {}
    return _SCHOOL_COMPLETION_STATUS


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


def prompt_excerpt(prompt_text: str | None) -> str | None:
    if not prompt_text:
        return None
    text = strip_markdown(prompt_text)
    if len(text) <= 220:
        return text
    return text[:217].rsplit(" ", 1)[0] + "..."


def shared_group_title_for_draft(draft_path: Path) -> str | None:
    rel = relative_to_root(draft_path)
    for group in shared_groups():
        for member in group.get("members", []):
            if member.get("draft_path") == rel:
                return group.get("title")
    return None


def shared_groups() -> list[dict]:
    global _SHARED_GROUPS
    if _SHARED_GROUPS is None:
        if SHARED_GROUPS_JSON.exists():
            _SHARED_GROUPS = json.loads(SHARED_GROUPS_JSON.read_text(encoding="utf-8"))
        else:
            _SHARED_GROUPS = []
    return _SHARED_GROUPS


def build_school_pages(
    school_entries: dict[str, list[dict[str, object]]],
    only_slugs: set[str] | None = None,
) -> None:
    schools_by_slug = school_metadata_by_slug()
    papers_by_slug = school_papers_by_slug()
    contributions_by_slug = school_major_contributions_by_slug()
    secondary_portals = secondary_portals_by_slug()
    completion_statuses = school_completion_status_by_slug()
    for slug, entries in school_entries.items():
        if only_slugs is not None and slug not in only_slugs:
            continue
        school = schools_by_slug.get(slug)
        if not school:
            continue
        page_path = OUTPUT_ROOT / "schools" / slug / "index.html"
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_html = PAGE_TEMPLATE.render(
            kind="school",
            page_title=school_display_name(school["name"]),
            favicon_href=favicon_href_for_output(page_path),
            school=school,
            papers=papers_by_slug.get(slug, []),
            major_contribution=contributions_by_slug.get(slug),
            secondary_portal=secondary_portals.get(slug),
            completion_status=completion_statuses.get(slug),
            entries=[
                {
                    **entry,
                    "href": html.escape(Path(str(entry["href"])).name)
                    if Path(str(entry["href"])).parent.name == "schools"
                    else html.escape(str(Path(str(entry["href"])).relative_to(f"schools/{slug}")))
                    if str(entry["href"]).startswith(f"schools/{slug}/")
                    else entry["href"],
                }
                for entry in entries
            ],
        )
        page_path.write_text(page_html, encoding="utf-8")


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
    parser.add_argument(
        "--school",
        action="append",
        default=[],
        help="Render only one school's draft pages and dashboard, e.g. --school wake-forest. May be repeated.",
    )
    args = parser.parse_args()

    all_drafts = [path for path in collect_drafts([]) if path.name.endswith(".draft.md")]
    if not all_drafts:
        raise SystemExit("No .draft.md files found to render.")

    target_inputs = [*args.targets, *[f"schools/{slug}" for slug in args.school]]
    full_build = not target_inputs
    if not full_build and not (OUTPUT_ROOT / "essays.html").exists():
        print("No existing review index found; running a full render instead.")
        full_build = True

    drafts = all_drafts if full_build else [path for path in collect_drafts(target_inputs) if path.name.endswith(".draft.md")]
    if not drafts:
        raise SystemExit("No matching .draft.md files found to render.")

    if full_build:
        clean_generated_pages()

    rendered = [(draft, render_draft_page(draft)) for draft in drafts]
    school_page_slugs = None if full_build else school_slugs_for_drafts(drafts)
    build_index(all_drafts, school_page_slugs=school_page_slugs)
    build_home_page()
    copy_public_assets()
    if full_build:
        print(f"Rendered {len(rendered)} review page(s) to {OUTPUT_ROOT}")
    else:
        school_count = len(school_page_slugs or set())
        print(
            f"Rendered {len(rendered)} targeted review page(s), "
            f"updated {school_count} school dashboard(s), and refreshed review/essays.html."
        )


if __name__ == "__main__":
    main()
