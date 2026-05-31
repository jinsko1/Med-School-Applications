# Shared Essay Sync

Use this when multiple schools ask functionally similar secondary prompts.

## Source Files
- Shared essay drafts live in `essays/shared-drafts/*.draft.md`.
- Group membership lives in `data/shared_essay_groups.json`.
- School-specific facts and tailoring still live in each school's `prompt-XX.local.md`.

## How It Works
Some school `prompt-XX.draft.md` files are symlinks to a shared draft. Editing the school draft or the shared draft edits the same file.

For example, if several schools ask for a challenge essay, they can all point to:

```text
essays/shared-drafts/challenge-resilience.draft.md
```

The review site still renders a separate page for each school prompt, with the actual prompt and local notes shown above the shared draft.

Shared drafts are only shared across schools. If two prompts at the same school match the same theme, only one is linked and the other stays as a standalone school-specific draft.

## Commands
Refresh the shared links after rebuilding school packets:

```bash
python3 scripts/sync_shared_essay_drafts.py
```

Preview grouping without changing files:

```bash
python3 scripts/sync_shared_essay_drafts.py --dry-run
```

Refresh reviewer pages:

```bash
python3 scripts/render_review_site.py
```

## Safety
The sync script links only untouched placeholder drafts by default. If a school draft has real writing in it, the script skips it unless you explicitly pass `--force`.
