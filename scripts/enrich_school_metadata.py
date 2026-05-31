#!/usr/bin/env python3
"""Add school-fit metadata and heuristic school-list estimates."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHOOLS_JSON = ROOT / "data" / "schools.json"
MSAR_SUMMARY_JSON = ROOT / "data" / "msar" / "2027" / "md_profiles_summary.json"
MSAR_PROFILE_DIR = ROOT / "data" / "msar" / "2027" / "profiles"
SCHOOLS_DIR = ROOT / "schools"

APPLICANT_ASSUMPTIONS = {
    "resident_state": "CA",
    "gpa": 3.73,
    "mcat": 520,
    "profile": "California applicant with strong research, clinical exposure, service with vulnerable communities, student advocacy, teaching, leadership, and scientific communication.",
}


MSAR_NAME_BY_SLUG = {
    "uc-davis": "University of California, Davis, School of Medicine",
    "ucsd": "University of California, San Diego School of Medicine",
    "kaiser-permanente": "Kaiser Permanente Bernard J. Tyson School of Medicine",
    "temple": "Lewis Katz School of Medicine at Temple University",
    "emory": "Emory University School of Medicine",
    "virginia-tech-carilion": "Virginia Tech Carilion School of Medicine",
    "vermont-larner": "Robert Larner, M.D., College of Medicine at the University of Vermont",
    "wisconsin": "University of Wisconsin School of Medicine and Public Health",
    "mcw": "Medical College of Wisconsin",
    "jefferson-kimmel": "Sidney Kimmel Medical College at Thomas Jefferson University",
    "miami-miller": "University of Miami Leonard M. Miller School of Medicine",
    "wake-forest": "Wake Forest University School of Medicine",
    "albany": "Albany Medical College",
    "drexel": "Drexel University College of Medicine",
    "wayne-state": "Wayne State University School of Medicine",
    "loyola-stritch": "Loyola University Chicago Stritch School of Medicine",
    "quinnipiac-netter": "Frank H. Netter MD School of Medicine at Quinnipiac University",
    "tulane": "Tulane University School of Medicine",
    "eastern-virginia": "Eastern Virginia Medical School",
    "rush": "Rush Medical College of Rush University Medical Center",
    "rosalind-franklin": "Chicago Medical School at Rosalind Franklin University of Medicine & Science",
    "new-york-medical-college": "New York Medical College",
    "uc-riverside": "University of California, Riverside School of Medicine",
    "cusm": "California University of Science and Medicine-School of Medicine",
    "umass-chan": "University of Massachusetts T.H. Chan School of Medicine",
    "nova-southeastern-md": "Nova Southeastern University Dr. Kiran C. Patel College of Allopathic Medicine",
    "roseman": "Roseman University College of Medicine",
    "hackensack-meridian": "Hackensack Meridian School of Medicine",
    "belmont-frist": "Thomas F. Frist, Jr. College of Medicine at Belmont University",
    "uicom": "University of Illinois College of Medicine",
    "george-washington": "George Washington University School of Medicine & Health Sciences",
    "california-northstate": "California Northstate University College of Medicine",
}


WHY_SCHOOL_FACTS = {
    "uc-davis": "UC Davis highlights a network of 11 student-run clinics serving regional primary-care needs, which gives you a concrete bridge from Hospice SLO, Restorative Partners, and Cal Poly student-health work to Northern/Central California service.",
    "ucsd": "UCSD introduces students to outpatient patient care in the first year through Clinical Foundations and ambulatory care apprenticeship, while offering focused PRIME pathways for equity, global health, and Indigenous health interests.",
    "kaiser-permanente": "Kaiser integrates foundational, clinical, and health-systems science across all four years and starts clinical exposure within the first weeks at Los Angeles-area Kaiser Permanente medical centers.",
    "temple": "Temple lets students train at the North Philadelphia campus or regional St. Luke's/WellSpan campuses, so the campus-interest essay can be made very specific to patient population and setting.",
    "emory": "Emory's curriculum includes a dedicated five-month research phase and clinical/community access through Grady, the Atlanta VA, the CDC, and the Carter Center ecosystem.",
    "virginia-tech-carilion": "Virginia Tech Carilion requires every student to complete a hypothesis-driven research project guided by a mentoring team and presented in a scholarly format.",
    "vermont-larner": "Larner's Vermont Integrated Curriculum begins patient interaction on the first day of orientation and emphasizes professionalism, cultural competence, prevention, and health systems.",
    "wisconsin": "UW is an integrated school of medicine and public health; its ForWard curriculum deliberately blends basic, clinical, and public-health sciences with community-based application.",
    "mcw": "MCW has three Wisconsin campuses, including Milwaukee, Green Bay, and Central Wisconsin, allowing a why-school essay to connect campus choice with urban, regional, or community-facing medicine.",
    "jefferson-kimmel": "Jefferson's JeffMD curriculum combines early longitudinal clinical experience, scholarly inquiry, and a humanities thread around the mission to serve, lead, and discover.",
    "miami-miller": "Miami Miller offers a dense clinical and research ecosystem with nearly 3,000 beds across six hospitals plus signature centers such as Bascom Palmer and the Diabetes Research Institute.",
    "wake-forest": "Wake Forest now frames its Winston-Salem and Charlotte regional campuses as innovation-quarter hubs, with first-week patient interaction and a curriculum built around inquiry, collaboration, and leadership.",
    "albany": "Albany Medical College is embedded in the Albany Med Health System, a large regional system with four hospitals, 1,520 beds, more than 800 physicians, and 125 outpatient locations.",
    "drexel": "Drexel's history combines Hahnemann and the Woman's Medical College of Pennsylvania, and its Foundations and Frontiers curriculum emphasizes population health, informatics, quality, safety, and team learning.",
    "wayne-state": "Wayne State's Detroit setting is central to its identity, giving you a strong place to connect restorative justice, health equity, and urban underserved clinical interests.",
    "loyola-stritch": "Stritch's Jesuit framing makes cura personalis, social justice, and service to under-resourced communities the natural center of a school-fit essay rather than decoration.",
    "quinnipiac-netter": "Netter pairs students with community physician preceptors one afternoon per week in the first two years and builds a Scholarly Reflection and Concentration Capstone into the curriculum.",
    "tulane": "Tulane's New Orleans context makes community health, disaster/public-health awareness, and local health disparities unusually central to secondary essays.",
    "eastern-virginia": "EVMS is community-oriented in Norfolk and makes exposure to medicine, future physician identity, and practical clinical fit central to its secondary prompts.",
    "rush": "Rush sits in the Illinois Medical District and emphasizes immediate M1 patient exposure, social determinants, humanism, and service to a diverse Chicago patient population.",
    "rosalind-franklin": "Chicago Medical School sits within Rosalind Franklin's interprofessional health-sciences campus, which is useful for essays about teamwork and healthcare teams.",
    "new-york-medical-college": "NYMC pairs students with a community physician preceptor beginning in the first month, giving a concrete clinical-training detail for a why-school paragraph.",
    "uc-riverside": "UCR's three-year Longitudinal Ambulatory Care Experience lets students follow a panel of patients under a physician mentor, directly supporting its Inland Southern California mission.",
    "cusm": "CUSM uses a clinical-presentation-based curriculum and frames its mission around social accountability and physician training for California's Inland Empire.",
    "umass-chan": "UMass Chan's Vista Curriculum emphasizes biomedical, clinical, and health-systems science, with longitudinal preceptors starting in the first weeks and a public-sector/underserved mission.",
    "nova-southeastern-md": "NSU MD uses a hybrid case- and problem-based curriculum that places patients at the center of learning and rewards applicants who can reason through ambiguity.",
    "roseman": "Roseman's Readiness Curriculum is built around social determinants, emerging technology, interprofessional teams, and GENESIS early experiential learning.",
    "hackensack-meridian": "Hackensack Meridian's Human Dimension course pairs students with families in the community across multiple years, making longitudinal community partnership a signature fit detail.",
    "belmont-frist": "Belmont Frist is a newer Nashville MD program built around whole-person care, case-based learning, early clinical exposure, service learning, ethics, and health-systems science.",
    "uicom": "UIC enrolls students across Chicago, Peoria, and Rockford and explicitly prepares physicians for both rural and urban practice with cultural humility.",
    "george-washington": "GW is located a few blocks from the White House and pairs public-health/policy proximity with a 17,000+ square-foot Clinical Learning and Simulation Skills Center.",
    "california-northstate": "California Northstate uses a clinical-presentation-based curriculum and explicitly emphasizes primary care, patient-centeredness, and social accountability in Northern California.",
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def load_msar_profiles() -> dict[str, dict]:
    summary = json.loads(MSAR_SUMMARY_JSON.read_text(encoding="utf-8"))
    by_name = {normalize(item["shortName"]): item for item in summary}
    profiles: dict[str, dict] = {}
    for slug, msar_name in MSAR_NAME_BY_SLUG.items():
        item = by_name.get(normalize(msar_name))
        if not item:
            continue
        profile_path = MSAR_PROFILE_DIR / f"{item['institutionId']}.json"
        if profile_path.exists():
            profiles[slug] = json.loads(profile_path.read_text(encoding="utf-8"))
    return profiles


def mat_data(profile: dict, mat_type: str) -> dict:
    for item in profile.get("medSchoolMatDatas") or []:
        if item.get("matType") == mat_type:
            return item
    return {}


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def school_state(school: dict, profile: dict | None) -> str:
    if profile and profile.get("overview", {}).get("state"):
        return str(profile["overview"]["state"])
    location = school.get("location") or ""
    if "," in location:
        return location.rsplit(",", 1)[-1].strip()
    return ""


def applicant_bucket(school: dict, profile: dict | None) -> str:
    state = school_state(school, profile)
    if state == APPLICANT_ASSUMPTIONS["resident_state"]:
        return "res"
    public_private = (profile or {}).get("overview", {}).get("publicPrivate")
    if public_private == "P":
        return "nonres"
    return "total"


def ratio(data: dict, bucket: str) -> float | None:
    numerator = safe_float(data.get(bucket))
    denominator = safe_float(data.get("total"))
    if bucket == "total":
        numerator = denominator
    if denominator <= 0:
        return None
    return numerator / denominator


def theme_fit_multiplier(school: dict, profile: dict | None) -> tuple[float, list[str]]:
    haystack = " ".join(
        [
            school.get("notes", ""),
            " ".join(theme for prompt in school.get("prompts", []) for theme in prompt.get("themes", [])),
            (profile or {}).get("medSchoolSelection", {}).get("selectionFactors", ""),
            (profile or {}).get("medSchoolInformation", {}).get("missionStatement", ""),
        ]
    ).lower()
    multiplier = 1.0
    reasons = []
    for key, label, boost in [
        ("research", "research alignment", 0.07),
        ("service", "service alignment", 0.07),
        ("underserved", "underserved/community alignment", 0.08),
        ("health equity", "health-equity alignment", 0.08),
        ("public health", "public-health alignment", 0.06),
        ("leadership", "leadership alignment", 0.05),
        ("community", "community alignment", 0.05),
        ("clinical", "clinical alignment", 0.04),
    ]:
        if key in haystack:
            multiplier += boost
            reasons.append(label)
    return min(multiplier, 1.28), reasons[:3]


def estimate_chance(school: dict, profile: dict | None) -> dict[str, object]:
    applicant_gpa = APPLICANT_ASSUMPTIONS["gpa"]
    applicant_mcat = APPLICANT_ASSUMPTIONS["mcat"]
    median_gpa = safe_float(school.get("median_gpa"))
    median_mcat = safe_float(school.get("median_mcat"))
    bucket = applicant_bucket(school, profile)

    base_percent = 4.0
    applied = interviewed = matric = {}
    if profile:
        applied = mat_data(profile, "APPLIED")
        interviewed = mat_data(profile, "INTERVIEWED")
        matric = mat_data(profile, "MATRIC")
        applied_count = safe_float(applied.get(bucket) if bucket != "total" else applied.get("total"))
        interviewed_count = safe_float(interviewed.get(bucket) if bucket != "total" else interviewed.get("total"))
        matric_count = safe_float(matric.get(bucket) if bucket != "total" else matric.get("total"))
        if applied_count > 0:
            interview_rate = interviewed_count / applied_count if interviewed_count else 0
            matric_rate = matric_count / applied_count if matric_count else 0
            base_percent = max(matric_rate * 230, interview_rate * 32, 1.2)

    mcat_multiplier = min(max(1 + (applicant_mcat - median_mcat) * 0.055, 0.72), 1.35) if median_mcat else 1
    gpa_multiplier = min(max(1 + (applicant_gpa - median_gpa) * 1.7, 0.72), 1.2) if median_gpa else 1
    fit_multiplier, fit_reasons = theme_fit_multiplier(school, profile)
    state = school_state(school, profile)
    public_private = (profile or {}).get("overview", {}).get("publicPrivate")
    geography_multiplier = 1.0
    geography_reason = "private or geography-neutral pool"
    if state == APPLICANT_ASSUMPTIONS["resident_state"]:
        geography_multiplier = 1.15
        geography_reason = "California resident applying in-state"
    elif public_private == "P":
        geography_multiplier = 0.72
        geography_reason = "public out-of-state penalty"

    raw = base_percent * mcat_multiplier * gpa_multiplier * fit_multiplier * geography_multiplier
    if median_mcat >= 516 or median_gpa >= 3.89:
        raw *= 0.86
    if "newer" in (school.get("notes") or "").lower():
        raw *= 1.12
    percent = int(round(min(max(raw, 1), 24)))

    if percent >= 13:
        label = "comparatively favorable"
    elif percent >= 8:
        label = "reasonable"
    elif percent >= 5:
        label = "possible"
    else:
        label = "reach"

    applied_count = safe_float(applied.get(bucket) if bucket != "total" else applied.get("total")) if profile else 0
    interviewed_count = safe_float(interviewed.get(bucket) if bucket != "total" else interviewed.get("total")) if profile else 0
    matric_count = safe_float(matric.get(bucket) if bucket != "total" else matric.get("total")) if profile else 0
    basis = (
        f"Heuristic, not a true admissions probability. Assumes CA resident, GPA {applicant_gpa:.2f}, MCAT {applicant_mcat}, "
        f"and strong research/service/clinical fit. Uses cached 2027 MSAR-style {bucket} applicant/interview/matriculant counts "
        f"({int(applied_count)} applied, {int(interviewed_count)} interviewed, {int(matric_count)} matriculated when available), "
        f"school medians GPA {median_gpa:g} / MCAT {median_mcat:g}, {geography_reason}, and {', '.join(fit_reasons) or 'general mission fit'}."
    )
    return {
        "estimated_admit_chance_percent": percent,
        "estimated_admit_chance_label": label,
        "estimated_admit_chance_basis": basis,
        "estimated_admit_chance_assumptions": APPLICANT_ASSUMPTIONS,
    }


def update_school_readme(school: dict) -> None:
    readme_path = SCHOOLS_DIR / school["slug"] / "README.md"
    if not readme_path.exists():
        return
    text = readme_path.read_text(encoding="utf-8")
    section = (
        "## School Metadata\n"
        f"- Why-school fact: {school['why_school_fact']}\n"
        f"- Heuristic list estimate: ~{school['estimated_admit_chance_percent']}%\n"
    )
    text = re.sub(r"\n## School Metadata\n.*?(?=\n## |\Z)", "\n", text, flags=re.S).rstrip() + "\n\n" + section
    readme_path.write_text(text, encoding="utf-8")


def main() -> None:
    schools = json.loads(SCHOOLS_JSON.read_text(encoding="utf-8"))
    profiles = load_msar_profiles()
    for school in schools:
        slug = school["slug"]
        profile = profiles.get(slug)
        school["why_school_fact"] = WHY_SCHOOL_FACTS[slug]
        school["why_school_fact_source"] = "Cached 2027 MSAR profile plus official admissions page listed in this school packet."
        school.update(estimate_chance(school, profile))
        update_school_readme(school)
    SCHOOLS_JSON.write_text(json.dumps(schools, indent=2), encoding="utf-8")
    print(f"Enriched {len(schools)} school metadata records.")


if __name__ == "__main__":
    main()
