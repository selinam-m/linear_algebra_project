# Video script — bullet notes per speaker

Target under 10:00. Rehearse once with a timer before recording. If the
rehearsal lands over 9:45, cut slide 5 to 20 seconds (say only "we checked it
three ways and they all agree").

Keep cameras on for all three. Share the slides, not the editor.

---

## Slide 1 — Title (A, 0:20)
- Name the project, name all three of us.
- One line: "we used least squares to ask what actually drives a course's
  rating at Yale."

## Slide 2 — Motivation and questions (A, 1:00)
- Students choose courses on two visible things: workload and teaching quality.
- Nobody knows which one actually moves the overall rating, or whether that
  differs by discipline.
- Most students read CourseTable rather than the evaluations themselves, so a
  second question: does CourseTable say the same thing?
- Read Q1 and Q2 off the slide, slowly. These are the questions we answer at the
  end, so the audience should hear them clearly.

## Slide 3 — Data (B, 1:15)
- Spring 2026, Yale OCE through Yale Course Search.
- Q4 overall is the response; Q8 workload and the mean of Q5/Q6 are the
  predictors. Say the actual question wording for Q8 — "relative to other Yale
  courses" — because the scale matters.
- 25 courses per discipline, drawn at random from the full eligible list with a
  fixed seed. Under 8 responses, dropped and replaced from a backup list.
- QC: blind re-entry gave a __% disagreement rate.
- Do not claim anything about students or majors. Courses.

## Slide 4 — Least squares (C, 1:30)
- $A\beta = y$ has no solution because $y$ isn't in the column space.
- So take the closest point in the column space instead — that's a projection.
- The residual has to be perpendicular to the subspace, which is literally
  $A^\mathsf{T}e = 0$, and expanding gives the normal equations.
- Point at the diagram while saying it. This is the rubric's math slide; don't
  rush it.
- $A^\mathsf{T}A$ is invertible because the columns are independent — workload
  and teaching quality aren't perfectly correlated, and we checked.

## Slide 5 — Checks (C, 0:45) — the cut candidate
- SVD gives the same $\hat\beta$ through the pseudoinverse.
- `lstsq` and `statsmodels` agree too.
- Orthogonality holds to about 1e-15 numerically.
- Condition number: $\kappa(A^\mathsf{T}A) = \kappa(A)^2$, which is why you
  watch it when predictors are correlated. Ours were small.

## Slide 6 — Q1 results (B, 1:30)
- Walk the figure left to right: workload panel, then teaching panel.
- Say which discipline is most workload-sensitive and by how much.
- Give one $R^2$ out loud.
- Error bars are bootstrap, 1000 resamples — say whether any interval crosses
  zero.

## Slide 7 — OCE vs CourseTable (B, 1:00)
- The professor rating correlates ___ with the overall course question and ___
  with the teaching questions.
- If the first is clearly higher: the professor score is partly the overall
  rating wearing a different name, which is why Model B's $R^2$ looks so good.
- Be careful with the wording — we are showing a pattern consistent with that,
  not proving how CourseTable computes anything.

## Slide 8 — Q2 hidden gems (A, 1:15)
- Explain the rule once: predicted rating from the model, actual rating, and a
  gem is a course sitting more than 2 standard residuals above the line.
- Name two gems.
- Then the size/discipline breakdown, and say plainly whether the cells are too
  small to conclude much.

## Slide 9 — Limitations and conclusion (C, 0:45)
- One term. Course-level data. Response bias. Ordinal scales treated as numeric.
  n = 25 per discipline.
- Then answer Q1 in one sentence and Q2 in one sentence. End there — don't trail
  off.

---

## Recording checklist
- [ ] All three cameras on and visible
- [ ] Slides shared, full screen
- [ ] One rehearsal done with a timer
- [ ] Final recording under 10:00
- [ ] File plays back before anyone closes anything
