# Final School Verification - 2026-05-30

This pass used the local cached `2027` MSAR dataset in [`data/msar/2027`](</Users/jinko/Desktop/Med School Applications/data/msar/2027>) together with your updated `520` MCAT ceiling, California residency, revised personal statement, and integrated work/activities content.

## Main Changes
- Added `University of Massachusetts Chan Medical School`
- Removed `Boston University Chobanian & Avedisian School of Medicine`
- Removed `University of Cincinnati College of Medicine`
- Removed `University of Colorado School of Medicine`
- Removed `Keck School of Medicine of USC`
- Removed `University of Rochester School of Medicine and Dentistry`
- Removed `University of Virginia School of Medicine`

## Why These Changes
- The removed schools all carried meaningfully higher risk in the cached MSAR profiles because of very high accepted GPA ranges, public out-of-state dynamics, or both.
- `UMass Chan` was the strongest replacement because its MSAR profile was friendlier on accepted and matriculant ranges while still fitting your service, research, and community-focused narrative.
- This revision favors a higher-probability final list over prestige stacking.

## Examples From The Cached MSAR Profiles
- `Keck`: accepted median `3.91 / 518`; nonresident interview rate about `3.5%`
- `Rochester`: accepted median `3.94 / 519`; nonresident interview rate about `10.4%`
- `Boston University`: accepted median `3.92 / 519`; nonresident interview rate about `9.8%`
- `UVA`: accepted median `3.96 / 520`; nonresident interview rate about `9.1%`
- `Colorado`: accepted median `3.91 / 516`; public out-of-state interview rate about `5.4%`
- `Cincinnati`: accepted median `3.93 / 515`; public out-of-state interview rate about `4.9%`
- `UMass Chan`: accepted median `3.86 / 514`; matriculant median `3.79 / 511`; nonresident interview rate about `14.0%`

## Current Direction
- After the later lower-tier expansion, I cut back schools that looked artificially favorable on raw stats but were riskier in practice because of regional or population-specific fit screens.
- `Charles R. Drew` was removed because its mission and prompt set are unusually centered on applicants with very strong underserved-community and adversity-specific alignment, and the cached MSAR demographics are heavily skewed toward disadvantaged and underserved matriculants.
- `Western Michigan` was removed because its secondary explicitly asks about your connection to Southwest Michigan, which makes it a poor “chance-improving” add unless you have a real tie.
- `Nova Southeastern MD` was added as the cleaner replacement because it stays under the GPA cap, avoids the same kind of regional-tie prompt burden, and remains mission-compatible with your service and research profile.
- Current active list size: `34`
- Active school generator source of truth: [`scripts/active_school_packets.py`](</Users/jinko/Desktop/Med School Applications/scripts/active_school_packets.py>)
- Active school dataset: [`data/schools.json`](</Users/jinko/Desktop/Med School Applications/data/schools.json>)
- Updated workbook: [`med_school_list_md.xlsx`](</Users/jinko/Desktop/Med School Applications/med_school_list_md.xlsx>)

If you want a truly live refresh from the current MSAR portal rather than the local cache, I can do that next once I can reach your signed-in browser session. Right now the local Chrome DevTools bridge is not exposed, so I cannot inspect the live MSAR tab from this workspace.
