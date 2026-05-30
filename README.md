# Med School Applications Workspace

This repository was generated on 2026-05-30 to support your VS Code + Codex workflow for the 2027 AMCAS cycle.

## What This Repo Does
- Normalizes your active school list into a reusable local dataset
- Creates primary essay planning files
- Creates school-by-school secondary packets
- Syncs overlapping prompts through shared backbone files in `essays/shared/`
- Preserves school-specific customization in local note files
- Generates Typst mirrors for cleaner review packets later

## Quick Start
1. Draft primary materials in `essays/primary/`.
2. Fill school research notes in `schools/*/research.md`.
3. Edit reusable backbones in `essays/shared/`.
4. Write actual essay drafts in `*.draft.md`.
5. Regenerate the repo packet files with:

```bash
python3 scripts/build_application_repo.py
```
6. Render polished review pages from your markdown drafts with:

```bash
python3 scripts/render_review_site.py
```

7. If you want presentation-ready packets later, open the matching `.typ` files in `schools/*/essays/`.

## Important Notes
- Prompt sets in this repo use the latest public sources I could verify on 2026-05-30. Some schools are using 2024 Admit.org archives; a smaller number use newer 2025-2026 prompts from alternate public advising sources where Admit.org did not expose the full prompt text.
- Treat every school packet as a strong drafting head start, not as a substitute for checking each school’s live portal when secondaries open.
- The active MD school list currently includes 34 schools.
- Typst source files are generated, but the Typst CLI is not installed in this workspace right now, so rendering was not run here.
