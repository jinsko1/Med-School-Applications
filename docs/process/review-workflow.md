# Review Workflow

## Goal
Write in markdown, but show mentors and reviewers something much cleaner than raw source files.

## Source Files
- Write actual essay drafts in `*.draft.md`
- Keep reusable language in `essays/shared/*.md`
- Keep school-specific strategy in `prompt-XX.local.md`
- Treat generated `prompt-XX-*.md` files as prompt/reference packets

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
- Prompt text when the draft belongs to a school secondary
- Local notes and school research in expandable sections
- A review index page at `review/index.html`

## Best Practice
- Share the rendered HTML page or print it to PDF from your browser
- Keep revising the markdown draft, then rerun the render script whenever you want a fresh review copy
