# School-List Estimates

The percentages shown in the review index are heuristic planning estimates, not true admissions probabilities.

## Where The Numbers Come From
- Cached 2027 MSAR-style school profiles in `data/msar/2027/profiles/*.json`.
- Cached applicant/interview/matriculant counts by residency category from each school's `medSchoolMatDatas` section.
- Cached accepted-student GPA and MCAT medians from `data/schools.json` and the MSAR profile summary.
- Applicant assumptions in `scripts/enrich_school_metadata.py`: California resident, GPA `3.73`, MCAT `520`, strong research/service/clinical/leadership profile.
- Mission-fit adjustments inferred from prompt themes, MSAR-style selection language, and your work/activities.

## Estimate Recipe
1. Pick the relevant residency bucket: California resident for California schools, out-of-state for public non-California schools, and total pool for private schools.
2. Compute a rough base from cached school selectivity: applicant-to-interview and applicant-to-matriculant counts.
3. Adjust for MCAT and GPA distance from the school's accepted-student medians.
4. Adjust for in-state or out-of-state context.
5. Add a small mission-fit adjustment for research, service, clinical, health-equity, public-health, leadership, and community alignment.

## How To Use
Use the percentage as a sorting signal. A `12%` school is not a promise; it means the school is comparatively more favorable than a `3%` school under the assumptions above.

If your final GPA or MCAT differs from these assumptions, rerun or edit `scripts/enrich_school_metadata.py`.
