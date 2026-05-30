# Live MSAR Verification - 2026-05-30

This pass used the signed-in live `2027` MSAR portal on `May 30, 2026`, not the local cache.

## List Changes
- Removed `Geisel School of Medicine at Dartmouth`
- Removed `Tufts University School of Medicine`
- Removed `The Ohio State University College of Medicine`
- Removed `University of Iowa Roy J. and Lucille A. Carver College of Medicine`

## Why These Four Were Cut
- `Iowa Carver`
  Live MSAR showed accepted median `3.92 / 516`, matriculant median `3.92 / 515`, and a public out-of-state profile. That is too stats-heavy for a list aimed at maximizing odds.
- `Ohio State`
  Live MSAR showed accepted median `3.92 / 516`, matriculant median `3.88 / 513`, and an out-of-state interview rate of about `5.2%`.
- `Geisel`
  Live MSAR showed accepted median `3.90 / 517`, matriculant median `3.87 / 516`, with no compensating state advantage.
- `Tufts`
  Live MSAR showed accepted median `3.91 / 516`, matriculant median `3.86 / 514`, making it harder to justify as a realistic private target.

## Key Keeps Confirmed By Live MSAR
- `UMass Chan`
  Accepted median `3.86 / 514`, matriculant median `3.79 / 511`, out-of-state interview rate about `14.0%`.
- `Roseman`
  Accepted median `3.79 / 510`, matriculant median `3.79 / 509`, out-of-state interview rate about `11.1%`.
- `Belmont`
  Accepted median `3.84 / 512`, matriculant median `3.84 / 511`, no Tennessee preference stated, out-of-state interview rate about `8.2%`.
- `UICOM`
  Accepted median `3.85 / 512`, matriculant median `3.86 / 511`, no separate in-state criteria stated, out-of-state interview rate about `4.6%`.
- `EVMS`
  Accepted median `3.82 / 513`, matriculant median `3.79 / 513`, out-of-state interview rate about `6.0%`.

## Important Cautions From The Live Portal
- `UC Riverside`
  Live MSAR says out-of-state applicants are only considered case-by-case and must show strong ties to Inland Southern California. This is fine for a California resident, but it is not a general-purpose safety for non-local applicants.
- `University of Wisconsin`
  Live MSAR says the committee seeks applicants with personal, professional, or educational connections to Wisconsin, the school, or its mission. I kept it, but it is not as clean a target as a generic private school.
- `Nova Southeastern MD`
  Live MSAR confirmed weaker out-of-state yield than I expected, with an out-of-state interview rate of about `2.6%`. I kept it only because the remaining under-`3.85` alternatives were even more tied to geography, mission-specific pipelines, or extra assessment burdens.

## Current Direction
- Final active list size: `30`
- Workbook: [`med_school_list_md.xlsx`](</Users/jinko/Desktop/Med School Applications/med_school_list_md.xlsx>)
- Active school source: [`scripts/active_school_packets.py`](</Users/jinko/Desktop/Med School Applications/scripts/active_school_packets.py>)
- Active school data: [`data/schools.json`](</Users/jinko/Desktop/Med School Applications/data/schools.json>)

This version is intentionally more conservative and is better aligned with the goal of turning your time and secondary effort into the highest practical chance of at least one MD acceptance.
