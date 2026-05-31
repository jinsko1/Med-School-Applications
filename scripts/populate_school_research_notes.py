#!/usr/bin/env python3
"""Populate school research notes with applicant-fit drafting angles."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHOOLS_JSON = ROOT / "data" / "schools.json"
SCHOOLS_DIR = ROOT / "schools"


EXPERIENCE_ANGLES = {
    "research": "- Research fit: foreground UTI/women's-health microbiology research, AAS iron-quantification work, Frost Scholar support, ASM/CSU BIOTECH/WCBSURC presentations, and AgarLens software development.",
    "clinical": "- Clinical fit: use the Cal Poly Health Center clinical assistant role, hospice companionship, and physician mentorship/shadowing to show patient-facing maturity.",
    "service": "- Service fit: center Hospice SLO and Restorative Partners juvenile hall work as sustained, direct service with vulnerable people rather than one-off volunteering.",
    "underserved": "- Underserved/community fit: connect restorative justice work, menstrual-product advocacy, DEI committee work, and hospice care to attention to structural barriers.",
    "leadership": "- Leadership fit: use ASI University Student Governor, BCSM Ambassador outreach, lab trainee mentorship, and Learning Assistant work as proof of collaborative leadership.",
    "teaching": "- Teaching/communication fit: use Chemistry Learning Assistant work, BCSM tours/panels, conference presentations, and the academic website to show clear explanation across audiences.",
    "diversity": "- Difference/belonging fit: draw from juvenile hall conversations, DEI committee listening, hospice communication beyond words, and reading fiction as practice inhabiting other perspectives.",
    "california": "- California fit: emphasize California upbringing/education, Cal Poly service, student health work, and interest in serving California communities when the school rewards regional commitment.",
    "public_health": "- Public-health fit: connect menstrual-product access, UTI/women's-health research, juvenile justice, and social determinants of health to prevention and equity.",
    "growth": "- Growth/reflection fit: use the frustrating repeated growth-curve work, hospice expectations vs. reality, or first restorative-justice visits to show humility and changed behavior.",
}


def slugify(value: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-"))


def prompt_haystack(school: dict) -> str:
    parts = [school.get("name", ""), school.get("notes", ""), school.get("location", "")]
    for prompt in school.get("prompts", []):
        parts.extend([prompt.get("title", ""), prompt.get("text", "")])
        parts.extend(prompt.get("themes", []))
    return "\n".join(str(part).lower() for part in parts if part)


def choose_angles(school: dict) -> list[str]:
    haystack = prompt_haystack(school)
    selected: list[str] = []

    rules = [
        ("california", ("california", "uc ", "riverside", "davis", "san diego", "kaiser", "northstate", "cusm", "inland", "regional")),
        ("research", ("research", "publications", "scholarly", "science", "biomedical", "innovation", "discovery")),
        ("clinical", ("clinical", "patient", "physician", "medicine", "health-related", "exposure to medicine")),
        ("service", ("service", "volunteer", "community", "mission", "others")),
        ("underserved", ("underserved", "under-resourced", "health disparities", "health equity", "social determinants", "inequity", "justice", "public health")),
        ("public_health", ("public health", "policy", "prevention", "population", "health disparities", "social determinants")),
        ("leadership", ("leadership", "team", "collaboration", "common objective", "campus", "contribution")),
        ("teaching", ("teaching", "learning", "education", "active learning", "communication", "mentor")),
        ("diversity", ("diversity", "difference", "belonging", "perspective", "cross-cultural", "worldview", "prejudice")),
        ("growth", ("challenge", "adversity", "setback", "humility", "wrong", "feedback", "ambiguity", "resilience")),
    ]

    for key, patterns in rules:
        if any(pattern in haystack for pattern in patterns):
            selected.append(EXPERIENCE_ANGLES[key])

    for fallback in ("research", "clinical", "service", "leadership"):
        if EXPERIENCE_ANGLES[fallback] not in selected:
            selected.append(EXPERIENCE_ANGLES[fallback])

    return selected[:7]


def strategy_for_prompt(prompt: dict) -> str:
    title = prompt.get("title", "Prompt")
    text = f"{title}\n{prompt.get('text', '')}".lower()
    if any(term in text for term in ("why ", "specific interest", "campus interest", "mission fit", "why cnu", "why gw")):
        angle = "tie the school mission to your research-service throughline, then add two named programs or clinical/community sites before submission"
    elif any(term in text for term in ("public health", "health equity", "underserved", "social determinants", "under-resourced", "justice")):
        angle = "lead with Restorative Partners, menstrual-product advocacy, hospice, or UTI/women's-health research depending on the wording"
    elif any(term in text for term in ("research", "publication", "scholarly")):
        angle = "use UTI research, AAS collaboration, conferences, Frost Scholar support, and AgarLens as one coherent research-growth arc"
    elif any(term in text for term in ("diversity", "difference", "belonging", "worldview", "perspective", "cross-cultural")):
        angle = "choose one close-contact story and focus on what changed in your behavior rather than making a broad diversity claim"
    elif any(term in text for term in ("challenge", "adversity", "setback", "wrong", "feedback", "ambiguity", "resilience")):
        angle = "use a concrete moment of humility, then show the behavioral adjustment you made afterward"
    elif any(term in text for term in ("leadership", "team", "collaboration", "common objective")):
        angle = "use ASI menstrual-product advocacy, lab training, Learning Assistant work, or BCSM Ambassador outreach as collaborative leadership"
    elif any(term in text for term in ("gap", "current", "application through matriculation", "coming year")):
        angle = "give a concise timeline of research, clinical work, service, and application-year responsibilities"
    elif any(term in text for term in ("academic", "mcat", "test", "education not continuous", "withdrawal")):
        angle = "answer directly and factually; avoid overexplaining unless there is a real issue to contextualize"
    elif any(term in text for term in ("reapplicant", "previously applied")):
        angle = "use N/A language unless you become a reapplicant"
    else:
        angle = "select the strongest matching activity and keep the reflection tied to medicine"
    return f"- `{title}`: {angle}."


def render_research_notes(school: dict) -> str:
    location = school.get("location") or "Location not listed"
    stats = []
    if school.get("median_gpa") is not None:
        stats.append(f"GPA {school['median_gpa']}")
    if school.get("median_mcat") is not None:
        stats.append(f"MCAT {school['median_mcat']}")
    stats_text = ", ".join(stats) if stats else "stats not listed"
    note = school.get("notes") or "Use the prompt packet and official school site to add named details."
    why_school_fact = school.get("why_school_fact") or "Add one verified, school-specific fact before drafting."
    admit_percent = school.get("estimated_admit_chance_percent")
    admit_label = school.get("estimated_admit_chance_label", "unrated")
    admit_basis = school.get("estimated_admit_chance_basis", "Estimate has not been generated yet.")
    prompt_strategies = "\n".join(strategy_for_prompt(prompt) for prompt in school.get("prompts", []))
    fit_angles = "\n".join(choose_angles(school))

    return f"""# {school['name']} Research Notes

> Drafting use: these notes translate your work/activities into school-fit angles. Before final submission, add 2-3 verified school-specific names such as programs, clinics, tracks, student groups, research centers, curriculum features, or community partners.

## Applicant Fit Snapshot
- School context: {location}; cached accepted-student medians: {stats_text}.
- Current list note: {note}
- Why-school fact: {why_school_fact}
- Estimated admit chance: ~{admit_percent}% ({admit_label}); {admit_basis}
- Core applicant narrative: research persistence, patient-facing humility, service with vulnerable communities, student advocacy, teaching/mentorship, and thoughtful communication.

## Experiences to Foreground
{fit_angles}

## Prompt Strategy
{prompt_strategies}

## Details to Add Before Submission
- Add exact school names for the program, clinic, curriculum element, or community partnership you would actually use in a final essay.
- Add one sentence explaining why that school detail fits your existing record rather than sounding like generic praise.
- Avoid repeating the same activity in every prompt for this school; distribute research, clinical care, service, advocacy, and teaching across the packet.
"""


def main() -> None:
    schools = json.loads(SCHOOLS_JSON.read_text(encoding="utf-8"))
    for school in schools:
        slug = school.get("slug") or slugify(school["name"])
        path = SCHOOLS_DIR / slug / "research.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_research_notes(school), encoding="utf-8")
    print(f"Updated {len(schools)} school research note file(s).")


if __name__ == "__main__":
    main()
