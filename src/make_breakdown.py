"""Build PROJECT_BREAKDOWN.pdf: intent, method, code and results in one document."""

import argparse
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

FONTS = Path("C:/Windows/Fonts")
INK = colors.HexColor("#15150f")
SOFT = colors.HexColor("#52514e")
RULE = colors.HexColor("#d8d7d0")
BLUE = colors.HexColor("#2a5fa5")
BAND = colors.HexColor("#f2f1ec")


def register_fonts():
    faces = [("Body", "georgia.ttf"), ("Body-Bold", "georgiab.ttf"),
             ("Body-Italic", "georgiai.ttf"), ("Head", "segoeuib.ttf"),
             ("Mono", "consola.ttf"), ("Mono-Bold", "consolab.ttf")]
    for name, filename in faces:
        pdfmetrics.registerFont(TTFont(name, str(FONTS / filename)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                  italic="Body-Italic")


def styles():
    s = getSampleStyleSheet()
    base = dict(fontName="Body", textColor=INK, leading=14.5, fontSize=9.8)
    return {
        "title": ParagraphStyle("title", fontName="Head", fontSize=21, leading=25,
                                textColor=INK, spaceAfter=3),
        "subtitle": ParagraphStyle("subtitle", fontName="Body-Italic", fontSize=11.5,
                                   leading=15, textColor=SOFT, spaceAfter=16),
        "h1": ParagraphStyle("h1", fontName="Head", fontSize=14.5, leading=18,
                             textColor=BLUE, spaceBefore=16, spaceAfter=7),
        "h2": ParagraphStyle("h2", fontName="Head", fontSize=11, leading=14,
                             textColor=INK, spaceBefore=11, spaceAfter=4),
        "body": ParagraphStyle("body", alignment=TA_JUSTIFY, spaceAfter=7, **base),
        "bullet": ParagraphStyle("bullet", leftIndent=12, bulletIndent=2,
                                 spaceAfter=3.5, **base),
        "mono": ParagraphStyle("mono", fontName="Mono", fontSize=8.1, leading=11.4,
                               textColor=INK, backColor=BAND, borderPadding=7,
                               spaceBefore=4, spaceAfter=9),
        "caption": ParagraphStyle("caption", fontName="Body-Italic", fontSize=8.4,
                                  leading=11, textColor=SOFT, spaceBefore=3,
                                  spaceAfter=13),
        "cell": ParagraphStyle("cell", fontName="Body", fontSize=8.6, leading=11.4,
                               textColor=INK),
        "cellmono": ParagraphStyle("cellmono", fontName="Mono", fontSize=7.9,
                                   leading=11, textColor=INK),
        "cellhead": ParagraphStyle("cellhead", fontName="Head", fontSize=8.6,
                                   leading=11.4, textColor=INK),
    }


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Body", 8)
    canvas.setFillColor(SOFT)
    canvas.drawString(20 * mm, 12 * mm, "Modeling Student Priorities")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(canvas.getPageNumber()))
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 15.5 * mm, A4[0] - 20 * mm, 15.5 * mm)
    canvas.restoreState()


def table(rows, widths, st, mono_cols=()):
    data = []
    for r, row in enumerate(rows):
        out = []
        for c, cell in enumerate(row):
            if r == 0:
                style = st["cellhead"]
            elif c in mono_cols:
                style = st["cellmono"]
            else:
                style = st["cell"]
            out.append(Paragraph(str(cell), style))
        data.append(out)
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, RULE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, RULE),
    ]))
    return t


def figure(path, width_mm, caption, st, flow):
    p = Path(path)
    if not p.exists():
        return
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(str(p)).getSize()
    w = width_mm * mm
    flow.append(Image(str(p), width=w, height=w * ih / iw))
    flow.append(Paragraph(caption, st["caption"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="PROJECT_BREAKDOWN.pdf")
    args = ap.parse_args()

    register_fonts()
    st = styles()
    f = []

    def para(text, style="body"):
        f.append(Paragraph(text, st[style]))

    def bullets(items):
        for item in items:
            f.append(Paragraph(item, st["bullet"], bulletText="\u2022"))
        f.append(Spacer(1, 5))

    def code(text):
        f.append(Paragraph(text.replace("\n", "<br/>").replace(" ", "&nbsp;"),
                           st["mono"]))

    oce = pd.read_csv("output/betas_oce.csv")
    ct = pd.read_csv("output/betas_ct.csv")
    ci = pd.read_csv("output/beta_ci.csv")
    gems = pd.read_csv("output/gems.csv")
    clean = pd.read_csv("data/processed/clean.csv")
    LAB = {"humanities": "Humanities", "social_sciences": "Social Sciences",
           "stem": "STEM"}

    # ---------------------------------------------------------------- title
    para("Modeling Student Priorities", "title")
    para("Using linear algebra to separate workload from teaching quality in "
         "Yale course ratings &mdash; a complete account of the project, from "
         "intent to results.", "subtitle")

    # ------------------------------------------------------------- 1 intent
    para("1. What the project set out to do", "h1")
    para("Students choose courses on two things they can see in advance: how "
         "much work a course demands, and how well it is taught. Which of the "
         "two actually drives a course's reputation is not obvious, and it is "
         "plausible that the answer differs between the humanities, the social "
         "sciences and the sciences. Most students consult CourseTable rather "
         "than the evaluations themselves, which raises a second question about "
         "whether the summary they read says the same thing as the underlying "
         "data.")
    para("The project states two questions and answers both.")
    bullets([
        "<b>Q1.</b> How much do workload and teaching quality each contribute "
        "to a course's overall rating in STEM, humanities and social science "
        "courses, and does CourseTable's summary data tell the same story as "
        "the raw evaluations?",
        "<b>Q2.</b> Which courses are &ldquo;hidden gems&rdquo; &mdash; rated "
        "far above what the model predicts from workload and teaching quality "
        "&mdash; and where do they occur?",
    ])
    para("Throughout, the unit of observation is a <i>course</i>, not a student "
         "and not a major. Each row is one course's set of evaluation averages, "
         "so nothing here supports a claim about what any individual student "
         "wants.")

    # ----------------------------------------------------------- 2 pipeline
    para("2. How the project runs, end to end", "h1")
    para("Three sources feed the analysis. CourseTable's published export "
         "decides <i>which</i> courses are eligible and supplies their catalogue "
         "details; Yale's Online Course Evaluations supply <i>what students "
         "said</i>; and the linear algebra runs on the resulting table of 75 "
         "rows. Every stage is a separate script so each can be rerun alone.")
    code(
        "coursetable.py      CourseTable export   ->  frame.csv        558 eligible courses\n"
        "sample_courses.py   frame.csv            ->  sampled.csv      25 per discipline, seeded\n"
        "   (collection from OCE)                 ->  collected/*.json 75 course pages\n"
        "ingest.py           collected/*.json     ->  oce_entries.csv  exact means and SDs\n"
        "clean.py            sheet + frame        ->  clean.csv        joined and validated\n"
        "model.py            clean.csv            ->  betas_*.csv      the least squares\n"
        "bootstrap.py        clean.csv            ->  beta_ci.csv      95% intervals\n"
        "gems.py             clean.csv            ->  gems.csv         large positive residuals\n"
        "compare.py          clean + betas        ->  compare.csv      OCE against CourseTable\n"
        "tables.py           output/              ->  table_*.tex      LaTeX fragments\n"
        "figures.py          clean + output       ->  report/figures/  five figures\n"
        "summary.py          output/              ->  printed summary"
    )
    para("<b>run_all.py</b> executes all of it in order. "
         "<b>run_all.py --test</b> runs the same pipeline against generated data "
         "from <b>make_test_data.py</b>, which exists so the code can be "
         "exercised without touching anything real.")

    f.append(PageBreak())

    # --------------------------------------------------------------- 3 data
    para("3. Data", "h1")

    para("3.1 Why CourseTable decides the sample", "h2")
    para("CourseTable publishes a per-term export: one file of ratings and one "
         "catalogue file, both keyed by course identifier. Taking the sampling "
         "frame from it rather than building a course list by hand removes a "
         "great deal of manual work and, more importantly, removes a judgement "
         "call from the design.")
    para("<b>coursetable.py</b> builds the frame. Its <b>discipline_of()</b> "
         "assigns each course using Yale's own distributional area tags &mdash; "
         "<b>Hu</b> to humanities, <b>So</b> to social sciences, <b>Sc</b> to "
         "the sciences. Two wrinkles had to be handled:")
    bullets([
        "Mathematics and computer science carry <i>no</i> area tag at all; Yale "
        "files them under the quantitative-reasoning <i>skill</i> instead. The "
        "skill tag is useless as a marker on its own, because 96 economics "
        "courses also carry it. Untagged courses whose <i>first-listed</i> "
        "subject is MATH, CPSC, S&amp;DS, AMTH or ENAS therefore join the "
        "sciences &mdash; 67 courses in all.",
        "Checking the first-listed subject rather than every cross-listing "
        "matters. &ldquo;YData: Data Science for Political Campaigns&rdquo; is "
        "listed as EP&amp;E, PLSC and S&amp;DS; matching any listing would have "
        "classified a political science course as STEM.",
        "Courses carrying two or more area tags are excluded as ambiguous.",
    ])
    para("A course enters the frame if it is a Yale College listing, has exactly "
         "one discipline under those rules, has at least 8 evaluation responses, "
         "and carries all three CourseTable figures. That leaves <b>558</b> "
         "courses: 223 humanities, 140 social science, 195 science.")

    para("3.2 Sampling", "h2")
    para("<b>sample_courses.py</b> draws 25 courses per discipline plus 10 "
         "ordered backups. The generator is seeded per discipline &mdash; "
         "<b>default_rng([2026, crc32(discipline)])</b> &mdash; so that changing "
         "or re-running one discipline never reshuffles the others. The script "
         "also writes the entry sheet with the sampled course codes already "
         "filled in, and refuses to overwrite a sheet that already holds data.")
    para("Only about 40% of eligible courses carry a CourseTable professor "
         "rating. Sampling freely would have left the CourseTable model roughly "
         "ten courses per discipline, too few to fit three parameters and "
         "bootstrap them, so the draw is restricted to courses that have one. "
         "The cost is that the sample represents courses CourseTable holds "
         "professor data for, not all Yale courses.")

    para("3.3 Collection", "h2")
    para("Each course page was read directly rather than searched for: the "
         "export supplies the CRN, and the term code is fixed at 202503, so the "
         "summary page for a course is addressable on its own. The response "
         "distributions sit behind a second endpoint, one request per question.")
    para("The important decision here is that we did <i>not</i> use the averages "
         "OCE prints. Those are rounded to one decimal place, which at 25 "
         "courses per discipline contributes roughly &plusmn;0.05 of noise to "
         "every variable &mdash; noise that attenuates exactly the correlations "
         "being measured. Instead each respondent's individual answer was "
         "recorded.")
    para("<b>ingest.py</b> converts those answers into numbers. "
         "<b>counts_of()</b> maps each answer word onto the 1&ndash;5 scale for "
         "its question &mdash; &ldquo;poor&rdquo; through "
         "&ldquo;excellent&rdquo; for the overall question, &ldquo;strongly "
         "disagree&rdquo; through &ldquo;strongly agree&rdquo; for the teaching "
         "questions, &ldquo;much less&rdquo; through &ldquo;much greater&rdquo; "
         "for challenge and workload &mdash; and raises on anything it does not "
         "recognise rather than guessing. <b>mean_sd()</b> then computes the "
         "mean and sample standard deviation from the counts.")
    para("Working from response level also gives the correct <i>n</i> for each "
         "question, which is not the course's response count: students skip "
         "questions, and in this sample a course's per-question n is usually "
         "below its response total.")

    para("3.4 Quality control", "h2")
    para("Because nothing is typed by hand, the risk is a parsing error rather "
         "than a transcription error, so blind re-entry would prove nothing. "
         "Three checks replace it, all in <b>clean.py</b> and all reported to "
         "<b>output/qc_report.txt</b>:")
    bullets([
        "<b>displayed_check()</b> compares each of the 375 computed means "
        "against the figure OCE displays. The largest discrepancy is 0.0500 "
        "&mdash; exactly the half-step of OCE's own rounding &mdash; and none "
        "falls outside it. This confirms the parse is correct for every value.",
        "<b>source_check()</b> compares CourseTable's response count against "
        "OCE's: all 75 agree exactly, confirming the two sources refer to the "
        "same course offering.",
        "<b>source_check()</b> also compares our area-tag discipline against "
        "OCE's own primary division. They agree on 69 of the 71 courses where "
        "OCE reports a comparable division. The two exceptions, EVST 3255 and "
        "NSCI 1600, are cross-listed courses whose department differs from the "
        "area the course itself carries; we keep the area tag, because it is "
        "attached to the course rather than to its department.",
    ])
    para("<b>clean.py</b> also joins the entry sheet to the frame and drops any "
         "course that fails validation. Discipline, enrollment, response count "
         "and the CourseTable columns all come from the frame rather than the "
         "sheet, so they cannot be mistyped, and a course code absent from the "
         "frame is rejected outright. No course was dropped: all 75 sampled "
         "courses had published evaluations, so no backups were needed.")

    f.append(PageBreak())

    # ---------------------------------------------------------------- 4 math
    para("4. The mathematics", "h1")

    para("4.1 The problem", "h2")
    para("Let x<sub>1</sub> be a course's workload mean, x<sub>2</sub> its "
         "instructional quality (the mean of the two teaching questions), and y "
         "its overall rating. For the n courses of one discipline, build the "
         "design matrix A whose rows are [1, x<sub>1i</sub>, x<sub>2i</sub>]. "
         "In general no \u03b2 satisfies A\u03b2 = y exactly, because y almost "
         "never lies in the three-dimensional subspace Col(A) inside "
         "<i>R</i><super>n</super>. The least-squares problem is to find the "
         "\u03b2\u0302 minimising ||y \u2212 A\u03b2||, which is the same as "
         "finding the point of Col(A) closest to y.")

    para("4.2 Normal equations and projection", "h2")
    para("That closest point is the orthogonal projection of y onto Col(A). The "
         "residual e = y \u2212 A\u03b2\u0302 must be orthogonal to every column "
         "of A, which is exactly A<super>T</super>e = 0; expanding gives the "
         "normal equations.")
    code("A\u1d40A \u03b2\u0302 = A\u1d40y          "
         "\u0177 = A\u03b2\u0302 = Py,    P = A(A\u1d40A)\u207b\u00b9A\u1d40\n"
         "e = y \u2212 \u0177,  A\u1d40e = 0      "
         "R\u00b2 = 1 \u2212 \u2016e\u2016\u00b2 / \u2016y \u2212 \u0233\u2016\u00b2")
    para("When the columns of A are linearly independent, A<super>T</super>A is "
         "invertible and \u03b2\u0302 is unique. Independence holds here as long as "
         "workload and instructional quality are not perfectly correlated across "
         "the sampled courses, which the code checks directly: the observed "
         "within-discipline correlations are 0.16, \u22120.05 and 0.32.")
    para("<b>model.py</b> implements this in <b>fit_ls()</b>. The solve is "
         "written out explicitly as <b>np.linalg.solve(A.T @ A, A.T @ y)</b> "
         "&mdash; the normal equations, not a library least-squares call. The "
         "same function then recomputes \u03b2\u0302 three other ways purely as "
         "a check: via the SVD pseudoinverse, via <b>np.linalg.lstsq</b>, and "
         "via statsmodels OLS, and reports whether all four agree.")

    para("4.3 SVD and conditioning", "h2")
    para("Writing A = U\u03a3V<super>T</super> gives the equivalent solution "
         "\u03b2\u0302 = V\u03a3<super>+</super>U<super>T</super>y through the "
         "pseudoinverse. The singular values also give the condition number "
         "\u03ba(A) = \u03c3<sub>max</sub>/\u03c3<sub>min</sub>. Because "
         "\u03ba(A<super>T</super>A) = \u03ba(A)<super>2</super>, forming the "
         "normal equations squares the conditioning, which is the standard "
         "reason to prefer an SVD or QR route when predictors are strongly "
         "correlated. Here \u03ba(A) runs from 1.05 to 3.88, so the squaring is "
         "harmless and the routes agree to machine precision.")

    para("4.4 Standardisation", "h2")
    para("<b>standardize()</b> subtracts the mean and divides by the sample "
         "standard deviation, applied within each discipline before fitting. "
         "This makes \u03b2\u0302<sub>1</sub> and \u03b2\u0302<sub>2</sub> "
         "directly comparable: each is the change in overall rating, in standard "
         "deviations, per one-standard-deviation change in its predictor. It "
         "also means the fit describes variation <i>within</i> a discipline "
         "only &mdash; a point that matters for how the results are read.")

    para("4.5 Uncertainty", "h2")
    para("<b>bootstrap.py</b>, in <b>intervals()</b>, resamples courses with "
         "replacement 1000 times within each discipline, refits by the same "
         "normal equations, and takes the 2.5th and 97.5th percentiles of each "
         "weight. The seed is fixed so the intervals reproduce exactly.")

    para("4.6 Hidden gems, and a rank trap", "h2")
    para("<b>gems.py</b> fits one <i>pooled</i> model across all 75 courses so "
         "that every course is judged on the same scale, adding discipline "
         "indicator columns. <b>pooled_design()</b> includes only <i>two</i> of "
         "the three indicators, with STEM as the omitted baseline. Including all "
         "three alongside the intercept would make the columns of A linearly "
         "dependent &mdash; the three dummies sum to the intercept column "
         "&mdash; so A<super>T</super>A would be singular and the solve would "
         "fail or return nonsense. A course is flagged when its standardised "
         "residual r<sub>i</sub> = e<sub>i</sub>/s exceeds 2, with "
         "s = \u221a(||e||<super>2</super>/(n\u2212p)). <b>find_gems()</b> falls "
         "back to the top 5% when fewer than three courses clear that bar, "
         "which is what happened.")

    f.append(PageBreak())

    # ---------------------------------------------------------------- 5 code
    para("5. The code, file by file", "h1")
    para("Every script takes its input path as a command-line flag and defaults "
         "to the real data, so any stage can be rerun alone or pointed at the "
         "test set.")
    rows = [["File", "What it does", "Key functions", "Writes"]]
    for a, b, c, d in [
        ("src/coursetable.py", "Builds the eligible-course frame from the "
         "CourseTable export", "discipline_of()", "data/processed/frame.csv"),
        ("src/sample_courses.py", "Draws the seeded sample and lays out the "
         "entry sheet", "has_entries()", "sampled.csv, oce_entries.csv"),
        ("src/ingest.py", "Turns collected pages into exact means, SDs and "
         "per-question n", "counts_of(), mean_sd()",
         "oce_entries.csv, qc_counts.csv, displayed.csv"),
        ("src/clean.py", "Joins sheet to frame, validates, runs the three QC "
         "checks", "displayed_check(), source_check(), size_bin()",
         "clean.csv, qc_report.txt, dropped_courses.csv"),
        ("src/model.py", "Least squares by the normal equations, with SVD and "
         "library cross-checks", "fit_ls(), standardize(), "
         "fit_by_discipline(), pooled_design()",
         "betas_oce.csv, betas_ct.csv, betas_robust.csv"),
        ("src/bootstrap.py", "95% confidence intervals by resampling courses",
         "intervals()", "beta_ci.csv"),
        ("src/gems.py", "Pooled residual model and the hidden-gem rule",
         "find_gems()", "gems.csv, gems_by_group.csv, residuals.csv"),
        ("src/compare.py", "Evaluations against CourseTable, including the "
         "circularity test", "corr()", "compare.csv"),
        ("src/tables.py", "Result tables as LaTeX fragments",
         "escape_cells(), write()", "output/table_*.tex"),
        ("src/figures.py", "All five figures, as PDF and PNG",
         "fig1_weights() &hellip; fig5_projection()", "report/figures/"),
        ("src/summary.py", "Prints every headline result in plain language",
         "main()", "&mdash; (stdout)"),
        ("src/entry_check.py", "Validates a part-filled sheet during manual "
         "collection", "main()", "&mdash; (stdout)"),
        ("src/make_test_data.py", "Generates labelled fake data so the pipeline "
         "can be tested", "counts_for_mean(), mean_of(), sd_of()",
         "data/test/"),
        ("run_all.py", "Runs every stage in order", "run()", "&mdash;"),
    ]:
        rows.append([a, b, c, d])
    f.append(table(rows, [34 * mm, 48 * mm, 40 * mm, 48 * mm], st,
                   mono_cols=(0, 2, 3)))
    f.append(Spacer(1, 6))
    para("One detail in <b>tables.py</b> is worth knowing about, because it "
         "would otherwise surface at the worst moment. Several real subject "
         "codes contain an ampersand &mdash; MB&amp;B, EP&amp;E, S&amp;DS "
         "&mdash; and an ampersand is LaTeX's column separator. "
         "<b>escape_cells()</b> escapes those before the tables are written; "
         "without it, every generated table fails to compile.")

    f.append(PageBreak())

    # ------------------------------------------------------------- 6 results
    para("6. Results", "h1")

    para("6.1 Q1: what carries a course's rating", "h2")
    rows = [["Discipline", "Workload", "Instructional quality", "R\u00b2"]]
    for _, r in oce.iterrows():
        c = ci[(ci.model == "oce") & (ci.discipline == r.discipline)]
        w = c[c.param == "workload"].iloc[0]
        t = c[c.param == "teaching"].iloc[0]
        rows.append([LAB[r.discipline],
                     f"{r.b_workload:+.2f} [{w.ci_lo:.2f}, {w.ci_hi:.2f}]",
                     f"<b>{r.b_teaching:.2f}</b> [{t.ci_lo:.2f}, {t.ci_hi:.2f}]",
                     f"{r.r2:.2f}"])
    f.append(table(rows, [36 * mm, 46 * mm, 50 * mm, 18 * mm], st))
    f.append(Spacer(1, 8))
    para("The result is the same in all three disciplines and is not subtle. "
         "Instructional quality carries almost the entire fit; workload carries "
         "essentially nothing, with the social-science estimate pointing in the "
         "opposite direction to the one usually assumed. Every teaching interval "
         "excludes zero and every workload interval contains it, so at this "
         "sample size the weight on workload cannot be distinguished from no "
         "effect at all. Because the predictors are nearly uncorrelated within "
         "discipline, this is not collinearity hiding a workload effect behind "
         "teaching quality.")
    figure("report/figures/fig1_weights.png", 150, "Figure 1. Standardized "
           "weights by discipline with 95% bootstrap intervals, for the "
           "evaluations and for CourseTable's summary figures.", st, f)

    para("6.2 A distinction the model cannot see", "h2")
    para("The finding above concerns variation <i>within</i> a discipline, "
         "because every variable is standardised within discipline before "
         "fitting. Between disciplines the picture differs: mean workload rises "
         "across the humanities, social sciences and STEM (2.86, 3.10, 3.32) "
         "while mean overall rating falls (4.33, 4.13, 3.80) &mdash; a perfectly "
         "inverse ordering. The design removes that variation deliberately, and "
         "with three disciplines it could not be tested anyway; the ordering is "
         "equally consistent with differing grading cultures or student "
         "populations. The defensible claim is narrow: among courses competing "
         "within one discipline, how hard a course is tells you nothing about "
         "how highly it is rated.")

    para("6.3 Q1c: does CourseTable agree?", "h2")
    rows = [["Discipline", "R\u00b2, evaluations", "R\u00b2, CourseTable",
             "Professor weight"]]
    for _, r in oce.iterrows():
        c = ct[ct.discipline == r.discipline].iloc[0]
        rows.append([LAB[r.discipline], f"{r.r2:.2f}", f"{c.r2:.2f}",
                     f"{c.b_ct_professor:.2f}"])
    f.append(table(rows, [36 * mm, 38 * mm, 38 * mm, 38 * mm], st))
    f.append(Spacer(1, 8))
    para("CourseTable's figures track the evaluations closely &mdash; its "
         "workload measure correlates with the OCE workload mean at r = 0.90, "
         "its course rating with the OCE overall mean at r = 0.83 &mdash; and "
         "the model has the same shape, with the professor rating carrying it "
         "and workload contributing nothing. But its explanatory power is "
         "markedly <i>lower</i>, which is the opposite of what the project "
         "anticipated. The cause is scope: CourseTable averages across past "
         "offerings, so it describes a course's reputation rather than the term "
         "measured, and that mismatch costs accuracy.")
    para("This also bears on whether CourseTable's professor rating is simply "
         "its course rating relabelled. It correlates 0.66 with the "
         "overall-course question and 0.60 with the teaching questions. The gap "
         "leans the way the hypothesis predicted but is far too small to support "
         "it; the professor rating looks like a genuinely distinct, "
         "instructor-level measurement.")
    figure("report/figures/fig4_circularity.png", 150, "Figure 2. CourseTable's "
           "professor rating against two different OCE questions. If the score "
           "were the overall rating relabelled, the left panel would be much "
           "the tighter of the two.", st, f)

    para("6.4 Q2: hidden gems", "h2")
    g = gems[gems.model == "oce"]
    rows = [["Course", "Discipline", "Class size", "Rating", "r<sub>i</sub>"]]
    for _, r in g.iterrows():
        rows.append([r.course_code, LAB[r.discipline], r.size_bin,
                     f"{r.actual_raw:.2f}", f"{r.residual_std:.2f}"])
    f.append(table(rows, [26 * mm, 36 * mm, 26 * mm, 22 * mm, 20 * mm], st))
    f.append(Spacer(1, 8))
    para("No course in the sample reached a standardised residual above 2, so "
         "the top-5% fallback applies. That the threshold caught nothing is "
         "itself the finding: a model explaining 69&ndash;86% of the variance "
         "leaves little room for a course to sit far above its prediction, so "
         "on this evidence the hidden gem is close to nonexistent. Applying the "
         "same rule to CourseTable's figures flags three courses &mdash; "
         "PLSC 3511, PHYS 0700 and MCDB 4820 &mdash; which share no members "
         "with the list above.")
    figure("report/figures/fig2_actual_vs_predicted.png", 115, "Figure 3. "
           "Actual against predicted overall rating, with the flagged courses "
           "labelled.", st, f)

    para("6.5 Robustness and numerical checks", "h2")
    para("Adding intellectual challenge as a third predictor changes nothing: "
         "teaching stays at 0.84, 0.88 and 0.93, workload stays indistinguishable "
         "from zero, challenge itself contributes little, and R\u00b2 moves by "
         "under 0.01 in every discipline. Across every fit, max |A<super>T</super>e| "
         "is below 8\u00d710<super>\u221215</super>, confirming numerically that "
         "the residual is orthogonal to the column space, and the normal-equation "
         "solution agreed with the SVD, lstsq and statsmodels solutions in every "
         "case.")

    f.append(PageBreak())

    # --------------------------------------------------------- 7 limitations
    para("7. What the results do not show", "h1")
    para("<b>The predictors and the response come from the same survey.</b> "
         "This is the limitation that most constrains what the results mean. "
         "Overall assessment, organisation and feedback are three items on one "
         "form, answered by the same student in the same sitting. A student who "
         "enjoyed a course tends to rate every item highly, so part of the 0.90 "
         "correlation between instructional quality and overall rating reflects "
         "a shared response disposition rather than teaching causing "
         "satisfaction. The high R\u00b2 should be read as evidence that these "
         "items move together, not as evidence that teaching quality determines "
         "a course's worth. Separating the two would need a measure of teaching "
         "collected independently of the students doing the rating, which no "
         "publicly available source provides.")
    para("The remaining limitations:")
    bullets([
        "One term only, so nothing speaks to change over time.",
        "Course-level rather than student-level data, so no claim about "
        "individual students or majors follows.",
        "Response bias: students who complete evaluations are not a random "
        "subset of those enrolled.",
        "Ordinal 1&ndash;5 scales treated as numeric and averaged.",
        "n = 25 per discipline, which the bootstrap intervals reflect.",
        "A sample restricted to courses for which CourseTable holds a professor "
        "rating.",
        "Class size unevenly distributed (40 seminars, 25 mid-sized, 10 "
        "lectures), so the size breakdown rests on thin cells and no conclusion "
        "is drawn from it.",
        "CourseTable's metrics are derived quantities, averaged over past "
        "offerings, whose definitions we do not control.",
    ])

    # ------------------------------------------------------------ 8 reproduce
    para("8. Reproducing this", "h1")
    code("python -m venv .venv\n"
         ".venv\\Scripts\\activate\n"
         "pip install -r requirements.txt\n\n"
         "python run_all.py --skip-sampling    # rebuild every table and figure\n"
         "python src\\summary.py               # print the headline results\n"
         "python run_all.py --test             # exercise the code on fake data")
    para("<b>--skip-sampling</b> leaves the frame and the course draw alone. "
         "Omitting it re-draws the sample, which would mean re-collecting all 75 "
         "courses from OCE. The seeds are fixed throughout, so a rerun "
         "reproduces the numbers in this document exactly.")
    para("The raw collected pages are kept in <b>data/raw/collected/</b> so "
         "nothing needs re-fetching, and the CourseTable export is kept in "
         "<b>data/coursetable/</b> so the frame can be rebuilt from scratch. "
         "<b>report/report.tex</b> and <b>slides/slides.tex</b> compile on "
         "Overleaf. <b>DECISIONS.md</b> records every choice made and why, "
         "including the ones that were reversed; <b>QUESTIONS.md</b> records "
         "what was asked, what was answered, and what is still open.")
    para("Course evaluation data stays in the private repository.")

    doc = SimpleDocTemplate(args.out, pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title="Modeling Student Priorities",
                            author="Selinam Mortey",
                            creator="Modeling Student Priorities",
                            subject="Linear algebra application project")
    doc.build(f, onFirstPage=footer, onLaterPages=footer)
    size = Path(args.out).stat().st_size
    print(f"wrote {args.out}  ({size/1024:.0f} KB, {doc.page} pages)")


if __name__ == "__main__":
    main()
