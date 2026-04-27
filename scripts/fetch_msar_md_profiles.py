#!/usr/bin/env python3
"""Cache 2027 MSAR MD profiles from a signed-in Chrome session."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from browser_control import BrowserControlError, open_page


DEFAULT_YEAR = 2027
DEFAULT_TARGET_INDEX = 0


def build_fetch_expression(batch: List[Dict[str, Any]], year: int) -> str:
    payload = json.dumps(batch, ensure_ascii=True)
    return f"""
(async () => {{
  const items = {payload};
  const year = {year};
  const out = [];
  for (const item of items) {{
    const response = await fetch(
      `https://api.mec.aamc.org/msar-service/medSchool/${{item.institutionId}}/profile/CURRENT_EDITION`,
      {{ credentials: "include" }}
    );
    if (!response.ok) {{
      throw new Error(`Profile fetch failed for ${{item.institutionId}}: ${{response.status}}`);
    }}
    const data = await response.json();
    out.push({{
      institutionId: item.institutionId,
      year,
      sourceProgram: item,
      profile: data[0]
    }});
  }}
  return out;
}})()
"""


def profile_gpa(profile: Dict[str, Any]) -> Any:
    for bucket in profile.get("medSchoolGpa", []):
        if bucket.get("gpaTypeName") != "School-Specific Accepted Applicants":
            continue
        for score in bucket.get("medSchoolGpaScores", []):
            if "Overall GPA" in (score.get("gpaScoreTitle") or ""):
                return score.get("median")
    return None


def profile_mcat(profile: Dict[str, Any]) -> Any:
    for bucket in profile.get("medSchoolMcat", []):
        if bucket.get("mcatTypeName") != "School-Specific Accepted Applicants":
            continue
        for score in bucket.get("medSchoolMcatScores", []):
            if "total MCAT" in (score.get("mcatScoreTitle") or ""):
                return score.get("median")
    return None


def summarize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    profile = entry["profile"]
    campus = (profile.get("campusList") or [{}])[0]
    financial = profile.get("medSchoolFinancial") or {}
    selection = profile.get("medSchoolSelection") or {}
    curriculum = profile.get("medSchoolCurriculum") or {}
    information = profile.get("medSchoolInformation") or {}
    return {
        "institutionId": entry["institutionId"],
        "msarYear": profile.get("msarYear"),
        "shortName": profile.get("shortName"),
        "city": campus.get("city"),
        "state": campus.get("stateCd"),
        "publicPrivate": information.get("publicPrivate"),
        "missionStatement": information.get("missionStatement"),
        "medianOverallGpa": profile_gpa(profile),
        "medianTotalMcat": profile_mcat(profile),
        "totalCostAttendRes": financial.get("totalCostAttendRes"),
        "totalCostAttendNonres": financial.get("totalCostAttendNonres"),
        "tuitionAndFeesRes": financial.get("tuitionAndFeesRes"),
        "tuitionAndFeesNonres": financial.get("tuitionAndFeesNonres"),
        "communityServicePct": selection.get("communityServicePct"),
        "researchPct": selection.get("researchPct"),
        "communityServiceReq": curriculum.get("communityServiceReq"),
        "researchPrograms": curriculum.get("researchPrograms"),
        "diversity": (profile.get("medSchoolStudLife") or {}).get("diversity"),
        "lastEditTime": profile.get("lastEditTime"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch 2027 MSAR MD profiles through a signed-in Chrome tab."
    )
    parser.add_argument("--target-index", type=int, default=DEFAULT_TARGET_INDEX)
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        default="data/msar/2027",
        help="Directory for cached MSAR profile files.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        _, session = open_page("127.0.0.1", 9222, None, args.target_index)
    except BrowserControlError as exc:
        raise SystemExit(str(exc)) from exc

    try:
        session._socket.settimeout(120)
        program_feed = session.evaluate(
            f"""
fetch(
  "https://cloudapi.platform.aamc.org/msar-data-feed/programs/by-type?programType=REG_MD&year={args.year}",
  {{ credentials: "include" }}
).then((r) => r.json())
"""
        )
        institution_ids = sorted(
            {item["institutionId"] for item in program_feed if item.get("institutionId")}
        )
        program_lookup = {
            item["institutionId"]: item for item in program_feed if item.get("institutionId")
        }
        full_entries: List[Dict[str, Any]] = []
        for start in range(0, len(institution_ids), args.batch_size):
            batch_ids = institution_ids[start : start + args.batch_size]
            batch = [program_lookup[item_id] for item_id in batch_ids]
            full_entries.extend(session.evaluate(build_fetch_expression(batch, args.year)))
    finally:
        session.close()

    profiles_dir = output_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    slim_entries = []
    for entry in full_entries:
        institution_id = entry["institutionId"]
        profile_path = profiles_dir / f"{institution_id}.json"
        profile_path.write_text(json.dumps(entry["profile"], indent=2, ensure_ascii=True))
        slim_entries.append(summarize_entry(entry))

    (output_dir / "md_program_feed.json").write_text(
        json.dumps(program_feed, indent=2, ensure_ascii=True)
    )
    (output_dir / "md_profiles_full_index.json").write_text(
        json.dumps(
            [
                {
                    "institutionId": entry["institutionId"],
                    "shortName": entry["profile"].get("shortName"),
                    "profilePath": f"profiles/{entry['institutionId']}.json",
                    "lastEditTime": entry["profile"].get("lastEditTime"),
                }
                for entry in full_entries
            ],
            indent=2,
            ensure_ascii=True,
        )
    )
    (output_dir / "md_profiles_summary.json").write_text(
        json.dumps(slim_entries, indent=2, ensure_ascii=True)
    )
    print(
        json.dumps(
            {
                "year": args.year,
                "institutionCount": len(institution_ids),
                "outputDir": str(output_dir),
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
