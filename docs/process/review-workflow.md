# Review Workflow

## Goal
Write in markdown, but show mentors and reviewers something much cleaner than raw source files.

## Source Files
- Write actual essay drafts in `*.draft.md`
- Keep reusable shared essay answers in `essays/shared-drafts/*.draft.md`
- Add school-specific strategy directly in the relevant `prompt-XX.draft.md`
- Use `data/schools.json` as the canonical prompt-title and limit source

## Render Review Pages
From the repo root:

```bash
python3 scripts/render_review_site.py
```

That command builds polished HTML review pages in `review/`.

## Render Only One Draft Or One Folder
```bash
python3 scripts/render_review_site.py essays/primary/amcas-personal-statement.draft.md
python3 scripts/render_review_site.py schools/uc-riverside
```

## What Reviewers Will See
- Your draft in a clean reading layout
- Basic title, limit, word-count, and character-count metadata
- Shared-source information when multiple schools use the same linked draft
- A review index page at `review/index.html`

## Best Practice
- Share the rendered HTML page or print it to PDF from your browser
- Keep revising the markdown draft, then rerun the render script whenever you want a fresh review copy
