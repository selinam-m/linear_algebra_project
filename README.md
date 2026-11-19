# Modeling Student Priorities

Linear algebra application project, Fall 2025 Yale course evaluations.

**Question.** When students rate a course overall, how much of that rating is
carried by how much work it demanded, and how much by how well it was taught?
And do the same two questions, asked of CourseTable's summary data, give the
same answer?

**Method.** Least squares by the normal equations, fitted separately per
discipline, on 75 randomly sampled courses.

---

## Results

Standardized weights — how many standard deviations the overall rating moves
per standard deviation of each predictor. Brackets are 95% bootstrap intervals
from 1000 resamples.

| Discipline | Workload | Instructional quality | R² |
|---|---|---|---|
| Humanities | −0.07 `[−0.25, 0.19]` | **0.84** `[0.68, 1.06]` | 0.69 |
| Social Sciences | +0.08 `[−0.14, 0.23]` | **0.89** `[0.63, 1.03]` | 0.79 |
| STEM | −0.05 `[−0.18, 0.12]` | **0.94** `[0.73, 1.11]` | 0.86 |

**Teaching quality carries the rating. Workload does not move it.** All three
teaching intervals exclude zero; all three workload intervals contain it. The
two predictors are nearly uncorrelated within discipline (r = 0.16, −0.05,
0.32), so this is not collinearity masking a workload effect.

**Hidden gems barely exist.** No course exceeded a standardized residual of 2.
Under the top-5% fallback: SOCY 2009 (1.79), ECON 4444 (1.67), MUSI 2240 (1.66),
CPSC 4670 (1.64). When a model explains 69–86% of the variance, little room is
left for a course to sit far above its prediction.

**CourseTable fits worse, not better.** R² = 0.55 / 0.43 / 0.28 against
0.69 / 0.79 / 0.86, because its figures average across past offerings rather
than describing the term measured. Its professor rating correlates 0.66 with
the OCE overall question and 0.60 with the teaching questions — too small a gap
to call it the course rating relabelled.

**One caveat governs all of it.** The response and both predictors are three
items on the same survey, answered by the same student in one sitting. Part of
the 0.90 correlation between instructional quality and overall rating is a
shared response disposition, not teaching causing satisfaction.

---

## Running it

```
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python run_all.py --skip-sampling   # rebuild every table and figure
python src\summary.py               # print the headline results
```

`--skip-sampling` leaves the sampling frame and the course draw alone. Omit it
only to re-draw the sample, which would mean re-collecting all 75 courses from
OCE. `python run_all.py --test` exercises the whole pipeline on generated data
and touches nothing real.

---

## Layout

| Path | What it holds |
|---|---|
| `src/` | the pipeline, one script per stage |
| `data/coursetable/` | CourseTable's published Fall 2025 export, two JSON files |
| `data/raw/collected/` | the 75 OCE pages as collected, one JSON per batch |
| `data/raw/` | the entry sheet, response counts, and OCE's displayed figures |
| `data/processed/` | `frame.csv` (558 eligible courses), `clean.csv` (the 75 analysed) |
| `output/` | result tables as CSV and as LaTeX fragments, plus the QC report |
| `report/` | `report.tex` and the five figures as PDF and PNG |
| `slides/`, `video/` | Beamer skeleton and the speaking notes |
| `PROJECT_BREAKDOWN.pdf` | full write-up of intent, method, code and results |

`report.tex` and `slides.tex` compile on Overleaf; there is no LaTeX install on
the machine this was built on.

---

## Pipeline

```
coursetable.py   CourseTable export  ->  frame.csv       eligible courses
sample_courses.py  frame             ->  sampled.csv     25 per discipline, seeded
     (collection from OCE)           ->  collected/*.json
ingest.py        collected           ->  oce_entries.csv exact means and SDs
clean.py         sheet + frame       ->  clean.csv       joined, validated
model.py         clean               ->  betas_*.csv     the least squares
bootstrap.py     clean               ->  beta_ci.csv     95% intervals
gems.py          clean               ->  gems.csv        large positive residuals
compare.py       clean + betas       ->  compare.csv     OCE against CourseTable
tables.py        output              ->  table_*.tex
figures.py       clean + output      ->  report/figures/
summary.py       output              ->  the printed summary
```

---

## Data provenance

Evaluation figures are not the one-decimal averages OCE displays. Each
respondent's individual answer was recorded and the means computed exactly, so
the analysis is not carrying ±0.05 of rounding noise on every variable at
n = 25.

Three checks, all in `output/qc_report.txt`:

- all 375 computed means sit within 0.0500 of OCE's displayed figure — exactly
  its rounding half-step, and none outside it
- CourseTable's response count matches OCE's for all 75 courses
- our discipline assignment matches OCE's own primary division on 69 of the 71
  courses where OCE reports a comparable one

Discipline comes from Yale's distributional area tags (`Hu`, `So`, `Sc`) rather
than a classification of our own. Mathematics and computer science carry no area
tag — Yale files them under the quantitative-reasoning skill — so untagged
courses whose first-listed subject is MATH, CPSC, S&DS, AMTH or ENAS join the
sciences.

Course evaluation data stays in this private repository.

---

## Division of work

| Member | Responsibility |
|---|---|
| A | Report §1–2, slides 1–2 and 8 |
| B | Results interpretation, report §5–6, slides 3, 6, 7 |
| Selinam | Pipeline, figures, report §3–4 and appendix, slides 4, 5, 9 |

Decisions and the reasoning behind them are logged in `DECISIONS.md`;
`QUESTIONS.md` records what was asked, answered, and still open.
