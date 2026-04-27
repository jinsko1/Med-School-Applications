#!/usr/bin/env python3
"""Rebuild the MD school list workbook from locally cached MSAR data."""

from __future__ import annotations

import argparse
import json
import math
import re
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET


NS_URI = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_URI = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"a": NS_URI}
XML_NS = f"{{{NS_URI}}}"
REL_NS = f"{{{REL_URI}}}"


@dataclass
class UserProfile:
    gpa: float = 3.73
    mcat_low: int = 514
    mcat_high: int = 520
    gpa_cap: float = 3.85
    mcat_floor: int = 508
    state: str = "CA"

    @property
    def mcat_mid(self) -> float:
        return (self.mcat_low + self.mcat_high) / 2


def cell_ref(col: str, row: int) -> str:
    return f"{col}{row}"


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def load_json(path: Path) -> List[Dict[str, object]]:
    return json.loads(path.read_text())


def normalize_name(value: str) -> str:
    value = value.lower()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def extract_text(*values: Optional[str]) -> str:
    return " ".join(v.strip() for v in values if isinstance(v, str) and v.strip())


def mission_score(profile: Dict[str, object], user: UserProfile) -> float:
    text = extract_text(
        profile.get("missionStatement"),
        profile.get("researchPrograms"),
        profile.get("diversity"),
    ).lower()
    score = 0.0
    keyword_weights = {
        "community": 2.0,
        "communities": 2.0,
        "service": 2.0,
        "underserved": 2.5,
        "diverse": 1.5,
        "diversity": 1.5,
        "equity": 2.0,
        "research": 1.5,
        "education": 1.0,
        "teach": 1.0,
        "lead": 1.0,
        "primary care": 1.0,
        "social": 1.0,
        "justice": 1.5,
        "population": 1.0,
        "populations": 1.0,
        "health": 0.5,
    }
    for needle, weight in keyword_weights.items():
        if needle in text:
            score += weight

    if profile.get("communityServiceReq") == "Y":
        score += 1.0

    community_pct = profile.get("communityServicePct")
    research_pct = profile.get("researchPct")
    if isinstance(community_pct, (int, float)):
        score += min(float(community_pct) / 20.0, 3.0)
    if isinstance(research_pct, (int, float)):
        score += min(float(research_pct) / 25.0, 2.5)

    if profile.get("state") == user.state:
        score += 2.0
    return score


def california_chance_score(profile: Dict[str, object], user: UserProfile) -> float:
    score = 0.0
    state = profile.get("state")
    public_private = profile.get("publicPrivate")
    if state == user.state:
        score += 4.0
    if public_private == "I":
        score += 2.0
    elif state == user.state:
        score += 2.5
    else:
        score -= 2.5

    community_pct = profile.get("communityServicePct")
    research_pct = profile.get("researchPct")
    if isinstance(community_pct, (int, float)) and community_pct >= 80:
        score += 0.75
    if isinstance(research_pct, (int, float)) and research_pct >= 85:
        score += 0.5
    return score


def stat_score(profile: Dict[str, object], user: UserProfile) -> float:
    gpa = float(profile.get("medianOverallGpa") or 0)
    mcat = float(profile.get("medianTotalMcat") or 0)
    gpa_distance = abs(gpa - user.gpa)
    mcat_distance = abs(mcat - user.mcat_low)
    return (gpa_distance * 10.0) + (mcat_distance * 0.9)


def classify_bucket(profile: Dict[str, object], user: UserProfile) -> str:
    gpa = float(profile.get("medianOverallGpa") or 0)
    mcat = float(profile.get("medianTotalMcat") or 0)
    if gpa <= user.gpa + 0.05 and mcat <= user.mcat_low:
        return "Safety"
    if gpa <= user.gpa + 0.12 and mcat <= user.mcat_mid:
        return "Target"
    return "Reach"


def choose_coa(profile: Dict[str, object]) -> Tuple[Optional[int], str]:
    state = profile.get("state") or ""
    public_private = profile.get("publicPrivate") or ""
    coa_res = profile.get("totalCostAttendRes")
    coa_nonres = profile.get("totalCostAttendNonres")
    if state == "CA" and coa_res:
        return int(coa_res), "CA public (in-state COA)" if public_private == "P" else "Private"
    if public_private == "P":
        if coa_nonres:
            return int(coa_nonres), "Public (out-of-state COA)"
        if coa_res:
            return int(coa_res), "Public (resident COA only)"
    if coa_nonres:
        return int(coa_nonres), "Private"
    if coa_res:
        return int(coa_res), "Private"
    return None, "Unavailable"


def build_note(profile: Dict[str, object], mission: float, bucket: str) -> str:
    parts = []
    if profile.get("state") == "CA":
        parts.append("California option")
    if mission >= 9:
        parts.append("strong mission fit")
    elif mission >= 6:
        parts.append("solid mission fit")
    if profile.get("communityServicePct"):
        parts.append(f"community-service emphasis {int(profile['communityServicePct'])}%")
    if profile.get("researchPct"):
        parts.append(f"research emphasis {int(profile['researchPct'])}%")
    if profile.get("communityServiceReq") == "Y":
        parts.append("community service required")
    if not parts:
        parts.append("selected for current MSAR stats and mission alignment")
    return f"{bucket} pick based on live MSAR data; " + "; ".join(parts) + "."


def restriction_status(restrictions: Iterable[str], user: UserProfile) -> str:
    text = " ".join(restrictions).lower()
    hard_exclusions = [
        "only in-state residents may apply",
    ]
    if any(needle in text for needle in hard_exclusions):
        return "hard"
    if "only applicants from" in text and user.state.lower() not in text:
        return "hard"

    conditional = [
        "must demonstrate strong ties to puerto rico",
        "must demonstrate strong ties to the state of new mexico",
        "must demonstrate strong ties to the state",
        "only those who have ties to/residency in wa",
        "seeks applicants from washington",
        "strong preference is given to wwami residents",
        "consider only those with ties to/residency in wa",
        "non-wwami residents will be considered if they have a tie to the region",
    ]
    if any(needle in text for needle in conditional):
        return "conditional"
    return "none"


def select_profiles(
    profiles: Iterable[Dict[str, object]],
    restrictions_by_id: Dict[int, List[str]],
    user: UserProfile,
    target_count: int,
    allow_relaxed_backups: bool,
    selection_mode: str,
) -> List[Dict[str, object]]:
    strict = []
    relaxed = []
    conditional = []
    for profile in profiles:
        institution_id = int(profile["institutionId"])
        restrictions = restrictions_by_id.get(institution_id, [])
        restriction_kind = restriction_status(restrictions, user)
        gpa = profile.get("medianOverallGpa")
        mcat = profile.get("medianTotalMcat")
        mission = profile.get("missionStatement")
        if gpa is None or mcat is None or not mission:
            continue
        if float(gpa) > user.gpa_cap:
            continue
        if restriction_kind == "hard":
            continue
        mission_fit = mission_score(profile, user)
        chance_fit = california_chance_score(profile, user)
        score = (mission_fit * 1.15) - stat_score(profile, user)
        if selection_mode == "soft":
            score = (mission_fit * 1.6) + (chance_fit * 1.4) - (stat_score(profile, user) * 0.7)
        enriched = dict(profile)
        enriched["restrictions"] = restrictions
        enriched["restrictionKind"] = restriction_kind
        enriched["missionFitScore"] = round(mission_fit, 2)
        enriched["californiaChanceScore"] = round(chance_fit, 2)
        enriched["statFitScore"] = round(stat_score(profile, user), 2)
        enriched["selectionScore"] = round(score, 2)
        enriched["bucket"] = classify_bucket(profile, user)
        coa_value, coa_basis = choose_coa(profile)
        enriched["selectedCoa"] = coa_value
        enriched["coaBasis"] = coa_basis
        enriched["notes"] = build_note(enriched, mission_fit, enriched["bucket"])
        if restriction_kind == "conditional":
            conditional.append(enriched)
        elif float(mcat) < user.mcat_floor:
            relaxed.append(enriched)
        else:
            strict.append(enriched)

    def sort_key(item: Dict[str, object]) -> tuple:
        return (
            -float(item["selectionScore"]),
            float(item["medianOverallGpa"]),
            float(item["medianTotalMcat"]),
            item["shortName"],
        )

    strict.sort(key=sort_key)
    relaxed.sort(key=sort_key)
    conditional.sort(key=sort_key)

    selected: List[Dict[str, object]] = []
    california = [item for item in strict if item.get("state") == user.state]
    selected.extend(california[: min(6, len(california))])
    selected_names = {item["shortName"] for item in selected}

    def extend_from(pool: List[Dict[str, object]], note_prefix: Optional[str] = None) -> None:
        for item in pool:
            if item["shortName"] in selected_names:
                continue
            if note_prefix:
                item = dict(item)
                item["notes"] = f"{note_prefix} {item['notes']}"
            selected.append(item)
            selected_names.add(item["shortName"])
            if len(selected) >= target_count:
                break

    extend_from(strict)
    if allow_relaxed_backups and len(selected) < target_count:
        extend_from(relaxed, "Lower-MCAT backup.")

    selected.sort(
        key=lambda item: (
            {"Safety": 0, "Target": 1, "Reach": 2}[str(item["bucket"])],
            float(item["medianOverallGpa"]),
            float(item["medianTotalMcat"]),
            item["shortName"],
        )
    )
    return selected[:target_count]


def make_inline_string_cell(ref: str, style: Optional[str], value: str) -> ET.Element:
    cell = ET.Element(f"{XML_NS}c", {"r": ref})
    if style is not None:
        cell.set("s", style)
    cell.set("t", "inlineStr")
    inline = ET.SubElement(cell, f"{XML_NS}is")
    text = ET.SubElement(inline, f"{XML_NS}t")
    if value.startswith(" ") or value.endswith(" ") or "\n" in value:
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text.text = value
    return cell


def make_numeric_cell(ref: str, style: Optional[str], value: object) -> ET.Element:
    cell = ET.Element(f"{XML_NS}c", {"r": ref})
    if style is not None:
        cell.set("s", style)
    cell.set("t", "n")
    v = ET.SubElement(cell, f"{XML_NS}v")
    v.text = str(value)
    return cell


def clone_row_template(row: ET.Element, row_number: int) -> ET.Element:
    new_row = deepcopy(row)
    new_row.set("r", str(row_number))
    for cell in new_row.findall(f"{XML_NS}c"):
        ref = cell.get("r", "")
        col = re.sub(r"\d+", "", ref)
        cell.set("r", cell_ref(col, row_number))
    return new_row


def replace_row_values(row: ET.Element, row_number: int, values: List[object]) -> ET.Element:
    style_by_col: Dict[str, Optional[str]] = {}
    for cell in row.findall(f"{XML_NS}c"):
        col = re.sub(r"\d+", "", cell.get("r", ""))
        style_by_col[col] = cell.get("s")
    for child in list(row):
        row.remove(child)
    row.set("r", str(row_number))
    columns = list("ABCDEFGHIJKL")
    for col, value in zip(columns, values):
        ref = cell_ref(col, row_number)
        style = style_by_col.get(col)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            row.append(make_numeric_cell(ref, style, value))
        else:
            row.append(make_inline_string_cell(ref, style, str(value)))
    return row


def update_md_sheet(
    archive: Dict[str, bytes],
    selected: List[Dict[str, object]],
    cache_summary_path: str,
) -> None:
    workbook = ET.fromstring(archive["xl/workbook.xml"])
    rels = ET.fromstring(archive["xl/_rels/workbook.xml.rels"])
    relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    md_sheet_rel = next(
        sheet.attrib[f"{REL_NS}id"]
        for sheet in workbook.find("a:sheets", NS)
        if sheet.attrib["name"] == "MD Schools"
    )
    sheet_path = relmap[md_sheet_rel].lstrip("/")
    if not sheet_path.startswith("xl/"):
        sheet_path = f"xl/{sheet_path}"
    tree = ET.fromstring(archive[sheet_path])
    sheet_data = tree.find(f"{XML_NS}sheetData")
    rows = list(sheet_data)
    header_template = rows[3]
    data_template = rows[4]

    for row in rows[4:]:
        sheet_data.remove(row)

    new_rows = []
    for index, profile in enumerate(selected, start=5):
        city = f"{profile.get('city')}, {profile.get('state')}"
        values = [
            profile["shortName"],
            "MD",
            city,
            profile["selectedCoa"] or "",
            profile["medianOverallGpa"],
            profile["medianTotalMcat"],
            profile["bucket"],
            profile["coaBasis"],
            f"MSAR cache: {cache_summary_path}",
            f"MSAR cache: {cache_summary_path}",
            profile["notes"],
            profile["missionStatement"] or "",
        ]
        row = clone_row_template(data_template, index)
        replace_row_values(row, index, values)
        new_rows.append(row)
    for row in new_rows:
        sheet_data.append(row)

    dimension = tree.find(f"{XML_NS}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:L{4 + len(selected)}")
    table = ET.fromstring(archive["xl/tables/table1.xml"])
    table.set("ref", f"A4:K{4 + len(selected)}")
    auto_filter = table.find(f"{XML_NS}autoFilter")
    if auto_filter is not None:
        auto_filter.set("ref", f"A4:K{4 + len(selected)}")
    sort_state = table.find(f"{XML_NS}sortState")
    if sort_state is not None:
        sort_state.set("ref", f"A5:K{4 + len(selected)}")

    archive[sheet_path] = ET.tostring(tree, encoding="utf-8", xml_declaration=False)
    archive["xl/tables/table1.xml"] = ET.tostring(table, encoding="utf-8", xml_declaration=False)


def update_summary_sheet(
    archive: Dict[str, bytes],
    selected: List[Dict[str, object]],
) -> None:
    workbook = ET.fromstring(archive["xl/workbook.xml"])
    rels = ET.fromstring(archive["xl/_rels/workbook.xml.rels"])
    relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    summary_rel = next(
        sheet.attrib[f"{REL_NS}id"]
        for sheet in workbook.find("a:sheets", NS)
        if sheet.attrib["name"] == "Summary"
    )
    sheet_path = relmap[summary_rel].lstrip("/")
    if not sheet_path.startswith("xl/"):
        sheet_path = f"xl/{sheet_path}"
    tree = ET.fromstring(archive[sheet_path])
    sheet_data = tree.find(f"{XML_NS}sheetData")
    rows = list(sheet_data)
    base_template = rows[0]

    summary_lines = [
        "Selection notes",
        f"This version keeps {len(selected)} MD schools and excludes any school above a live MSAR median GPA of 3.85.",
        "Mission fit was weighted toward community service, research, diversity, education, leadership, and California ties using locally cached 2027 MSAR profiles.",
        "COA, GPA, and MCAT values now come from your local MSAR cache rather than older public web sources.",
        "Buckets remain relative only: Safety means lower relative risk, not a guarantee.",
    ]

    for row in rows:
        sheet_data.remove(row)
    for idx, text_value in enumerate(summary_lines, start=1):
        row = clone_row_template(base_template, idx)
        replace_row_values(row, idx, [text_value])
        sheet_data.append(row)

    dimension = tree.find(f"{XML_NS}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:A{len(summary_lines)}")
    archive[sheet_path] = ET.tostring(tree, encoding="utf-8", xml_declaration=False)


def write_xlsx(path: Path, archive: Dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in archive.items():
            zf.writestr(name, data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild med_school_list_md.xlsx from cached MSAR data."
    )
    parser.add_argument(
        "--cache-summary",
        default="data/msar/2027/md_profiles_summary.json",
        help="Summary cache JSON produced by fetch_msar_md_profiles.py",
    )
    parser.add_argument(
        "--workbook",
        default="med_school_list_md.xlsx",
        help="Workbook to update in place.",
    )
    parser.add_argument(
        "--output-json",
        default="data/msar/2027/recommended_md_schools.json",
        help="Write the selected list here.",
    )
    parser.add_argument(
        "--program-feed",
        default="data/msar/2027/md_program_feed.json",
        help="Program feed JSON produced by fetch_msar_md_profiles.py",
    )
    parser.add_argument("--target-count", type=int, default=35)
    parser.add_argument(
        "--allow-relaxed-backups",
        action="store_true",
        help="Allow lower-MCAT backups if strict filters do not reach target count.",
    )
    parser.add_argument(
        "--selection-mode",
        choices=["hard", "soft"],
        default="hard",
        help="Use hard stat filtering only, or mission/chance-weighted soft ranking.",
    )
    parser.add_argument("--user-gpa", type=float, default=3.73)
    parser.add_argument("--mcat-low", type=int, default=514)
    parser.add_argument("--mcat-high", type=int, default=520)
    parser.add_argument("--gpa-cap", type=float, default=3.85)
    parser.add_argument("--mcat-floor", type=int, default=508)
    parser.add_argument("--state", default="CA")
    args = parser.parse_args()

    user = UserProfile(
        gpa=args.user_gpa,
        mcat_low=args.mcat_low,
        mcat_high=args.mcat_high,
        gpa_cap=args.gpa_cap,
        mcat_floor=args.mcat_floor,
        state=args.state,
    )
    cache_summary_path = Path(args.cache_summary)
    program_feed_path = Path(args.program_feed)
    workbook_path = Path(args.workbook)
    output_json_path = Path(args.output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    profiles = load_json(cache_summary_path)
    program_feed = load_json(program_feed_path)
    restrictions_by_id = {
        int(item["institutionId"]): item.get("restrictions") or []
        for item in program_feed
        if item.get("institutionId")
    }
    selected = select_profiles(
        profiles,
        restrictions_by_id,
        user,
        args.target_count,
        allow_relaxed_backups=args.allow_relaxed_backups,
        selection_mode=args.selection_mode,
    )

    archive: Dict[str, bytes] = {}
    with zipfile.ZipFile(workbook_path) as zf:
        for name in zf.namelist():
            archive[name] = zf.read(name)

    update_md_sheet(archive, selected, args.cache_summary)
    update_summary_sheet(archive, selected)
    write_xlsx(workbook_path, archive)
    output_json_path.write_text(json.dumps(selected, indent=2, ensure_ascii=True))
    print(
        json.dumps(
            {
                "selectedCount": len(selected),
                "workbook": str(workbook_path),
                "outputJson": str(output_json_path),
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
