# Application Workflow

## Recommended Order
1. Finish AMCAS personal statement and Work/Activities.
2. Write actual drafts in `*.draft.md` files so regeneration never overwrites your essay text.
3. Edit shared draft sources in `essays/shared-drafts/` when multiple schools use the same answer.
4. Run `python3 scripts/sync_shared_essay_drafts.py` after school-list or prompt changes.
5. Render clean review pages from your markdown drafts with `python3 scripts/render_review_site.py`.

## Editing Rules For This Repo
- Write your actual essay answer in `prompt-XX.draft.md`.
- If a school draft is a symlink, editing it also edits the shared source in `essays/shared-drafts/`.
- Prompt titles and limits come from `data/schools.json`.
