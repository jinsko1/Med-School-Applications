#!/usr/bin/env python3
"""Link reusable secondary drafts to shared source files.

The generator creates one draft file per school prompt. This script groups the
prompts that can reasonably share an essay core and replaces untouched prompt
draft placeholders with symlinks to `essays/shared-drafts/*.draft.md`.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHOOLS_JSON = ROOT / "data" / "schools.json"
OUTPUT_JSON = ROOT / "data" / "shared_essay_groups.json"
SHARED_DRAFT_DIR = ROOT / "essays" / "shared-drafts"
PLACEHOLDER = "Write your current draft here."


@dataclass(frozen=True)
class GroupRule:
    group_id: str
    title: str
    description: str
    title_patterns: tuple[str, ...] = ()
    theme_patterns: tuple[str, ...] = ()


GROUP_RULES: tuple[GroupRule, ...] = (
    GroupRule(
        "reapplicant-update",
        "Reapplicant Update",
        "Use only if you are reapplying. Otherwise leave the shared answer as N/A language.",
        ("reapplicant", "previously applied", "applied to medical school"),
        (),
    ),
    GroupRule(
        "additional-info",
        "Additional Information",
        "Use for optional updates or anything-else prompts. Keep it concise unless the school invites a substantive update.",
        ("anything else", "additional information", "application updates", "helpful context", "updates and context"),
        ("additional-info",),
    ),
    GroupRule(
        "current-and-gap-year",
        "Current Activities / Gap Year",
        "Use for prompts asking what you are doing from application through matriculation or explaining time away from school.",
        ("current", "recent activit", "gap", "coming year", "time gap", "full-time activity", "education not continuous"),
        ("gap-year",),
    ),
    GroupRule(
        "academic-context",
        "Academic Context",
        "Use for academic inconsistencies, test-context, course-load, discontinuity, or prior-program explanation prompts.",
        ("academic inconsist", "academic or test", "test inconsist", "mcat preparation", "standardized tests", "underloaded", "education not continuous", "incomplete prior program"),
        ("academic-context",),
    ),
    GroupRule(
        "challenge-resilience",
        "Challenge / Resilience",
        "Use for prompts about obstacles, adversity, conflict, ambiguity, resilience, or growth after difficulty.",
        ("challenge", "obstacle", "resilience", "adversit", "conflict", "ambiguity", "difficult"),
        ("challenge",),
    ),
    GroupRule(
        "diversity-community",
        "Diversity / Community Contribution",
        "Use for prompts about perspective, belonging, difference, community identity, and class contribution.",
        ("diversity", "difference", "perspective", "belonging", "community identity", "class contribution", "cross-cultural"),
        ("diversity-equity", "community"),
    ),
    GroupRule(
        "service-public-health",
        "Service / Public Health / Underserved",
        "Use for prompts about service, social determinants, public health, advocacy, inequity, and underserved communities.",
        ("service", "underserved", "public health", "social determinants", "health inequ", "health disparities", "under-resourced"),
        ("service",),
    ),
    GroupRule(
        "teamwork-leadership",
        "Teamwork / Leadership",
        "Use for prompts about team roles, collaboration, leadership, and working toward a shared goal.",
        ("teamwork", "leadership", "team", "common objective", "collaboration"),
        ("teamwork",),
    ),
    GroupRule(
        "future-goals",
        "Future Goals",
        "Use for prompts about the physician you want to become, future health care change, or combined-degree goals.",
        ("future", "career goals", "ten years", "healthcare progress", "md mph"),
        ("future-goals",),
    ),
)


def slugify(value: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-"))


def classify_prompt(prompt: dict) -> GroupRule | None:
    title = str(prompt.get("title", "")).lower()
    text = str(prompt.get("text", "")).lower()
    themes = {str(theme).lower() for theme in prompt.get("themes", [])}
    haystack = f"{title}\n{text}"

    for rule in GROUP_RULES:
        if any(pattern in haystack for pattern in rule.title_patterns):
            return rule
        if any(pattern in themes for pattern in rule.theme_patterns):
            return rule
    return None


def make_shared_draft(rule: GroupRule) -> Path:
    SHARED_DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    path = SHARED_DRAFT_DIR / f"{rule.group_id}.draft.md"
    if not path.exists():
        path.write_text(
            f"""# {rule.title} Shared Draft

{rule.description}

Write the reusable essay core here. Keep school-specific names, programs, and final tailoring in each school's local notes file.
""",
            encoding="utf-8",
        )
    return path


def is_placeholder(path: Path) -> bool:
    if not path.exists() or path.is_symlink():
        return True
    text = path.read_text(encoding="utf-8")
    return PLACEHOLDER in text and len(text.strip()) < 260


def link_draft(draft_path: Path, shared_path: Path, force: bool) -> str:
    if not force and not is_placeholder(draft_path):
        return "skipped-existing-draft"
    if draft_path.exists() or draft_path.is_symlink():
        draft_path.unlink()
    relative_target = Path(
        *[".."] * len(draft_path.parent.relative_to(ROOT).parts),
        shared_path.relative_to(ROOT),
    )
    draft_path.symlink_to(relative_target)
    return "linked"


def build_groups(force: bool, dry_run: bool) -> list[dict]:
    schools = json.loads(SCHOOLS_JSON.read_text(encoding="utf-8"))
    groups: dict[str, dict] = {}

    for school in schools:
        slug = school["slug"]
        for idx, prompt in enumerate(school.get("prompts", []), start=1):
            rule = classify_prompt(prompt)
            if rule is None:
                continue
            shared_path = make_shared_draft(rule)
            draft_path = ROOT / "schools" / slug / "essays" / f"prompt-{idx:02d}.draft.md"
            groups.setdefault(
                rule.group_id,
                {
                    "id": rule.group_id,
                    "title": rule.title,
                    "description": rule.description,
                    "shared_draft": str(shared_path.relative_to(ROOT)),
                    "members": [],
                },
            )
            status = "missing-draft"
            if draft_path.exists() or draft_path.is_symlink():
                status = "dry-run" if dry_run else link_draft(draft_path, shared_path, force)
            groups[rule.group_id]["members"].append(
                {
                    "school": school["name"],
                    "school_slug": slug,
                    "prompt_index": idx,
                    "prompt_title": prompt["title"],
                    "draft_path": str(draft_path.relative_to(ROOT)),
                    "status": status,
                }
            )

    return sorted(groups.values(), key=lambda item: item["title"])


def write_readme(groups: list[dict]) -> None:
    lines = [
        "# Shared Essay Drafts",
        "",
        "Edit these files when multiple schools ask functionally similar prompts.",
        "Linked school draft files are symlinks, so opening one of those school drafts edits the shared source directly.",
        "",
        "Use each school's `prompt-XX.local.md` file for school-specific names, programs, and final tailoring.",
        "",
    ]
    for group in groups:
        lines.extend(
            [
                f"## {group['title']}",
                f"- Shared draft: `{group['shared_draft']}`",
                f"- Linked prompts: {len(group['members'])}",
                "",
            ]
        )
    SHARED_DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    (SHARED_DRAFT_DIR / "README.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Link similar school essay drafts to shared markdown drafts.")
    parser.add_argument("--force", action="store_true", help="Replace existing non-placeholder draft files with shared links.")
    parser.add_argument("--dry-run", action="store_true", help="Show grouping output without changing draft links.")
    args = parser.parse_args()

    groups = build_groups(force=args.force, dry_run=args.dry_run)
    if not args.dry_run:
        OUTPUT_JSON.write_text(json.dumps(groups, indent=2), encoding="utf-8")
        write_readme(groups)

    linked = sum(1 for group in groups for member in group["members"] if member["status"] == "linked")
    skipped = sum(1 for group in groups for member in group["members"] if member["status"] == "skipped-existing-draft")
    print(f"Grouped {sum(len(group['members']) for group in groups)} prompt(s) across {len(groups)} shared draft(s).")
    print(f"Linked {linked}; skipped existing drafts {skipped}.")


if __name__ == "__main__":
    main()
