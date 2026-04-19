# Application Workflow

## Recommended Order
1. Finish AMCAS personal statement and Work/Activities.
2. Fill school research files in `schools/*/research.md`.
3. Draft shared backbone essays in `essays/shared/`.
4. Write actual drafts in `*.draft.md` files so regeneration never overwrites your essay text.
5. Run `python3 scripts/build_application_repo.py` whenever you want regenerated school packets.
6. Add school-specific tailoring in each `prompt-XX.local.md` file.
7. Render clean review pages from your markdown drafts with `python3 scripts/render_review_site.py`.

## Editing Rules For This Repo
- Edit shared themes when multiple schools overlap.
- Edit `prompt-XX.local.md` when only one school needs the change.
- Write your actual essay answer in `prompt-XX.draft.md`.
- Treat generated `prompt-XX.md` files as synced working packets rather than the source of truth.
- Treat generated `prompt-XX.typ` files as presentation-ready mirrors of the markdown packets.
