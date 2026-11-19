# DECISIONS.md

Settled choices. Change one only with a reason, and amend the row rather than
deleting it.

| # | Question | Decision | Status |
|---|---|---|---|
| D1 | Term | Fall 2025 only | settled |
| D2 | Discipline assignment | **Yale's own distributional areas**: `Hu`→Humanities, `So`→Social Sciences, `Sc`→STEM. An untagged course joins STEM only if its *first-listed* subject is MATH, CPSC, S&DS, AMTH or ENAS. Courses carrying two or more areas are excluded as ambiguous | settled |
| D3 | Courses | 25 per discipline = 75 total, + 10 ordered backups each. Eligible pools: 223 humanities / 140 social sciences / 195 STEM | settled (cut from 30) |
| D4 | Minimum responses | n_responses ≥ 8, applied when the frame is built, from CourseTable's `evaluation_statistic.responses`. Every later drop is logged to `output/dropped_courses.csv` | settled |
| D5 | Is OCE Q4 numeric? | **Yes.** Confirmed from an OCE summary page: "What is your overall assessment of this course?", 1-poor to 5-excellent, displayed as mean ± SD | settled |
| D6 | Teaching-quality predictor | mean of Q5 (well organized) and Q6 (clear feedback) | settled, confirmed against the live form |
| D7 | Extra predictor | Q7 intellectual challenge, collected for all courses, used only in the robustness model | settled |
| D8 | Hidden-gem threshold | standardized residual > 2; if fewer than 3 qualify, also report the top 5% | settled |
| D9 | CourseTable access | moot — the Fall 2025 export is in the repo, so nobody has to log in | closed |
| D10 | Submission | due time unconfirmed; one person submits, other two confirm | open |

## Decisions added beyond the plan

| # | Question | Decision |
|---|---|---|
| D11 | Data granularity | **Response-level.** Each respondent's individual answer to Q4–Q8 was collected for all 75 courses, and means, SDs and per-question *n* computed from those. OCE's displayed figures are rounded to one decimal, which at n=25 would add ~±0.05 of noise per variable. The Dept/Division/School benchmark columns are deliberately not collected |
| D21 | How OCE was read | Course pages fetched from within the signed-in session, addressed directly by `termCode=202503` and the CRN that CourseTable's export supplies. No searching was needed. ~450 throttled requests |
| D22 | QC, now that nothing is hand-typed | The risk is parse error, not transcription, so blind re-entry is meaningless here. Replaced by three checks: computed vs OCE-displayed means (375 values), CourseTable vs OCE response counts (75), and our discipline vs OCE's primary division (71 comparable) |
| D15 | What x₂ is called | "Instructional quality" in the report, never "professor rating". It is a course-level quantity: a professor teaching three courses produces three values, and OCE has no item rating a person |
| D16 | Why Q2 and Q7 are excluded from x₂ | Q2 (engagement) measures a student state confounded with prior interest in the subject; Q7 (intellectual challenge) measures course difficulty and would collide with the workload predictor. Q5 and Q6 are the only items describing instructor behaviour |
| D17 | Where CourseTable's export is used | Everything except the OCE question figures: sampling frame, discipline, title, instructors, enrollment, response count and all three CourseTable columns. The OCE sheet carries only the ten numbers that must be read off a page |
| D18 | Sampling restricted to courses with a professor rating | Yes. Only ~40% of eligible courses carry `average_professor_rating`; sampling freely would leave Model B about 10 courses per discipline. **Limitation to state:** the sample represents courses CourseTable holds professor data for, not all Yale courses |
| D19 | Which CourseTable rating | `average_rating`, the figure a student actually sees. `average_rating_same_professors` was considered and rejected as not being what students act on |
| D20 | CourseTable's scope | **All-time, not Fall 2025.** 287 courses with zero Fall 2025 responses still carry a rating, so the figure aggregates across offerings. Model B is therefore a comparison between prior reputation and what this term's students said — not a second measurement of the same thing |
| D12 | Pooled gem model rank | Two discipline dummies plus the intercept, STEM as baseline. All three dummies plus an intercept would make AᵀA singular |
| D13 | Standardization for the pooled model | Standardize within discipline before pooling, so a discipline's scale does not drive the residuals |
| D14 | LaTeX | Sources in-repo, compiled on Overleaf |
