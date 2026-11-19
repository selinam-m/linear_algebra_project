# Clarifying questions and answers

Running log. Every time a question is asked and answered, it gets an entry here
so the team can see what was decided and why without rereading chat history.

---

## 2026-11-19

### Q1. Where does the project live?
**Answer:** `C:\Users\morte\la-project`, its own top-level folder.
**Reason:** kept separate from the DDCA/Verilog coursework. Avoids OneDrive sync
conflicting with Git.

### Q2. How is OCE data captured?
**Answer:** Seli signs into Yale Course Search and navigates course to course;
the numbers are read off each rendered page and written into the CSV directly.
Hand entry stays the fallback.
**Reason:** the slow part of this project is transcription, not navigation.
Reading the page that is already on screen removes the digit-by-digit typing
without changing where the data comes from. Nothing is generated or estimated —
every number traces to a specific OCE page.
**Open risk:** if OCE renders its distributions in a popup or canvas that cannot
be read as text, this falls back to screenshot transcription. Test on course 1.

### Q3. Response counts or means?
**Answer:** means only for the full sample; full response counts for the ~15-course
QC subset.
**Reason:** 25 count cells per course across 75 courses is ~1,900 cells, and the
analysis never uses anything but the means. Keeping counts on a subsample is a
stronger check than blind re-entry alone: the mean can be recomputed from the
distribution and compared to the mean OCE reports.
**Depends on:** OCE actually displaying a mean per question (decision D5). If it
only shows a distribution, counts become mandatory for every course.

### Q4. How many courses per discipline?
**Answer:** 25 per discipline, 75 total, plus 10 ordered backups each.
**Reason:** taken from the plan's own cut list, applied now rather than at hour
five. Well above the 10-course minimum. n = 25 with 3 predictors leaves 21
degrees of freedom, which the bootstrap can work with.

### Q5. LaTeX toolchain?
**Answer:** `.tex` sources written in this repo, compiled on Overleaf.
**Reason:** no `pdflatex` on this machine. A MiKTeX install would cost ~30 min of
deadline buffer for no gain, since the report has to be shared with two other
people anyway.

### Q6. What defines "professor quality" when no OCE question rates a professor?
**Answer:** x₂ = mean of Q5 ("the course was well organized to facilitate student
learning") and Q6 ("I received clear feedback that improved my learning"),
reported as **instructional quality**.
**Reason:** of the five numeric items, Q4 is the response variable, Q2
(engagement) measures a student state confounded with prior interest in the
subject, and Q7 (intellectual challenge) measures course difficulty and would
collide with the workload predictor. Q5 and Q6 are the only two items on the
form that describe what the instructor did. Calling the result "instructional
quality" rather than "professor rating" is deliberate: it is attached to a
course, not a person.
**Robustness, free to run:** refit with Q5 alone, with Q6 alone, and with Q2
added, and report whether the ordering of the disciplines changes.

### Q7. Which term?
**Answer:** Fall 2025.
**Reason:** team decision; it is also the term whose CourseTable export is being
downloaded, so the two sources line up.

### Q8. What gets recorded from each OCE page?
**Answer:** the mean and the standard deviation of Q4–Q8. Not the
Dept/Division/School benchmark columns.
**Reason:** the page prints each figure as `3.0±1.0`, so the SD arrives with the
mean at no extra cost, and it supports a sentence about how much students
disagreed. The benchmark columns were considered and dropped to keep the sheet
narrow enough for three people to read.

### Q9. How much of the work does the CourseTable export absorb?
**Answer:** undecided until the Fall 2025 JSON has been inspected.
**Reason:** if the export carries subject, number, title, enrollment and season
for every course, it can supply the sampling frame as well as the three
CourseTable columns, which removes the hand-listing step entirely. If it is
thinner than that, only the three columns come from it.

---

## Open questions (need a person or a page to resolve)

| # | Question | Blocks | Who |
|---|---|---|---|
| ~~O1~~ | ~~Is OCE Q4 numeric, and does the page show a mean?~~ | — | **Resolved: yes, 1–5, mean ± SD** |
| ~~O2~~ | ~~Are the question numbers still Q4/Q5/Q6/Q7/Q8?~~ | — | **Resolved: yes, exactly as assumed** |
| ~~O3~~ | ~~Does CourseTable's rating refer to one term or to all offerings?~~ | — | **Resolved: all offerings** |
| O4 | Canvas due *time* | everything | Seli |
| ~~O8~~ | ~~Does every sampled course have a released OCE page?~~ | — | **Resolved: all 75 did, no backups needed** |
| ~~O5~~ | ~~Can B and A log into CourseTable?~~ | — | **Moot: the export is in the repo** |
| ~~O6~~ | ~~Is the response count shown on the OCE course page?~~ | — | **Moot: the export carries it** |
| ~~O7~~ | ~~Is CourseTable's rating simply the Q4 mean?~~ | — | **Resolved: no, it is a cross-offering average** |
| O8 | Does every sampled course actually have a released OCE page? | whether backups get used | Seli, during collection |

---

## 2026-11-19, after the CourseTable export arrived

### Q10. Is CourseTable's rating the same number as OCE's Q4 for this term?
**Answer:** No. 287 courses have zero Fall 2025 responses yet still carry an
`average_rating`, so the figure aggregates across past offerings of the same
course.
**Consequence:** Model B is not a re-measurement of Fall 2025. It compares the
reputation a student sees *before* enrolling against what that term's students
actually reported. `ct_scope` is `all-time`. This is a better question than the
plan assumed, and it needs saying explicitly in the write-up — otherwise the
comparison looks like a tautology.

### Q11. How is discipline assigned now?
**Answer:** Yale's own distributional area tags (`Hu`, `So`, `Sc`), with an
explicit subject list for untagged math and computer science.
**Reason:** using the registrar's classification removes a judgment call we would
otherwise have to defend. The exception exists because Yale files MATH, CPSC and
S&DS under the QR *skill* rather than an area, and QR is useless as a STEM
marker since 96 ECON courses carry it too. The fallback checks only the
first-listed subject, so a course cross-listed with S&DS is not dragged into
STEM against its primary listing.
**Excluded:** 35 courses carrying two or more area tags, as ambiguous.

### Q12. Why is the sample drawn only from courses with a professor rating?
**Answer:** only ~40% of eligible courses have `average_professor_rating`.
Sampling freely would leave Model B roughly 10 courses per discipline, too few
for three parameters plus a bootstrap.
**Cost:** the sample represents courses CourseTable holds professor data for,
not all Yale courses. This belongs in the limitations paragraph.
