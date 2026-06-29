# Med School Applications Workspace

This repository was generated on 2026-05-30 to support your VS Code + Codex workflow for the 2027 AMCAS cycle.

## What This Repo Does
- Normalizes your active school list into a reusable local dataset
- Creates primary essay planning files
- Creates school-by-school secondary packets
- Syncs overlapping prompts through shared backbone files in `essays/shared/`
- Links functionally similar essay drafts through `essays/shared-drafts/`
- Preserves school-specific customization in local note files
- Generates Typst mirrors for cleaner review packets later

## Quick Start
1. Draft primary materials in `essays/primary/`.
2. Review fit-focused school research notes in `schools/*/research.md`.
3. Edit reusable backbones in `essays/shared/`.
4. Write actual essay drafts in `*.draft.md`. Some are linked to shared source drafts in `essays/shared-drafts/`.
5. Regenerate the repo packet files with:

```bash
python3 scripts/build_application_repo.py
```
6. Refresh shared essay links after packet regeneration with:

```bash
python3 scripts/sync_shared_essay_drafts.py
```

7. Refresh school fit notes from the current school list and work/activities themes with:

```bash
python3 scripts/enrich_school_metadata.py
python3 scripts/populate_school_research_notes.py
```

8. Render polished review pages from your markdown drafts with:

```bash
python3 scripts/render_review_site.py
```

For a faster targeted rebuild after editing one school, use:

```bash
python3 scripts/render_review_site.py --school wake-forest
```

You can also target a single draft or prompt packet:

```bash
python3 scripts/render_review_site.py schools/wake-forest/essays/prompt-05.draft.md
python3 scripts/render_review_site.py schools/wake-forest/essays/prompt-05-commitment.md
```

Targeted rendering updates the matching essay page(s), any affected school dashboard(s), and `review/essays.html` without regenerating every essay page.

9. Refresh PubMed-based school research paper blurbs when needed with:

```bash
python3 scripts/fetch_school_research_papers.py
```

10. If you want presentation-ready packets later, open the matching `.typ` files in `schools/*/essays/`.

## Important Notes
- Prompt sets in this repo use the latest public sources I could verify on 2026-05-30. Some schools are using 2024 Admit.org archives; a smaller number use newer 2025-2026 prompts from alternate public advising sources where Admit.org did not expose the full prompt text.
- Treat every school packet as a strong drafting head start, not as a substitute for checking each school’s live portal when secondaries open.
- The active MD school list currently includes 32 schools.
- Shared draft sync details live in `docs/process/shared-essay-sync.md`.
- School-list percentages are heuristic prioritization estimates, not real admissions probabilities. Details live in `docs/process/school-list-estimates.md`.
- School research paper blurbs are curated PubMed-affiliated results stored in `data/school_research_papers.json`; weak matches are intentionally left blank, and any paper should still be verified before naming it in a final essay.
- Major contribution cards live in `data/school_major_contributions.json`; read the writer note because some are alumni, parent-university, namesake, or health-system contributions rather than discoveries made directly inside the current MD program.
- Live secondary portal links live in `data/secondary_portals.json`; add new schools there as portals arrive.
- Completed secondary essay checkmarks live in `data/school_completion_status.json`; add a school slug there when every secondary essay for that school is done.
- Typst source files are generated, but the Typst CLI is not installed in this workspace right now, so rendering was not run here.
