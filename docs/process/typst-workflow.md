# Typst Workflow

## Why Typst Is In This Repo
- Markdown remains the easiest place to draft and diff essay content.
- Typst mirrors each prompt packet so you can later render cleaner review packets without manually reformatting everything.
- Shared essay backbones still live in `essays/shared/`; Typst is layered on top rather than replacing that source of truth.

## Current State
- Typst source files are generated in `typst/` and beside each prompt file in `schools/*/essays/`.
- The Typst CLI is not installed in this workspace right now, so these files are ready for later rendering but were not compiled here.

## Recommended Use
1. Draft and revise in Markdown first.
2. Keep overlapping essays synced through `essays/shared/`.
3. Use `python3 scripts/render_review_site.py` for clean HTML review pages right now.
4. When you want cleaner PDF-style packets later, render the matching `.typ` files once Typst is installed.
