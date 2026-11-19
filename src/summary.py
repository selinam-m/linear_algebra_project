"""Print every headline result in plain language. Run after run_all.py."""

import argparse
from pathlib import Path

import pandas as pd

LABEL = {"humanities": "Humanities", "social_sciences": "Social Sciences", "stem": "STEM"}


def rule(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clean", default="data/processed/clean.csv")
    args = ap.parse_args()

    clean = pd.read_csv(args.clean)
    oce = pd.read_csv("output/betas_oce.csv")
    ct = pd.read_csv("output/betas_ct.csv")
    rob = pd.read_csv("output/betas_robust.csv")
    ci = pd.read_csv("output/beta_ci.csv")
    gems = pd.read_csv("output/gems.csv")
    comp = pd.read_csv("output/compare.csv")

    def metric(name, scope="all"):
        hit = comp[(comp["metric"] == name) & (comp["discipline"] == scope)]["value"]
        return float(hit.iloc[0]) if len(hit) else float("nan")

    rule("THE SAMPLE")
    print(f"  {len(clean)} courses, Fall 2025, drawn at random with a fixed seed")
    for d, n in clean["discipline"].value_counts().sort_index().items():
        sub = clean[clean["discipline"] == d]
        print(f"    {LABEL[d]:<16} {n:>3} courses, "
              f"mean rating {sub['overall'].mean():.2f}, "
              f"mean workload {sub['workload'].mean():.2f}")
    print(f"  class size: " + ", ".join(
        f"{k} {v}" for k, v in clean["size_bin"].value_counts().items()))

    rule("Q1  WHAT DRIVES A COURSE'S OVERALL RATING")
    print("  Standardized weights: how many SDs the rating moves per SD of predictor.")
    print(f"\n  {'discipline':<17}{'workload':>22}{'teaching':>22}{'R^2':>8}")
    for _, r in oce.iterrows():
        c = ci[(ci.model == "oce") & (ci.discipline == r.discipline)]
        w = c[c.param == "workload"].iloc[0]
        t = c[c.param == "teaching"].iloc[0]
        print(f"  {LABEL[r.discipline]:<17}"
              f"{r.b_workload:>8.2f} [{w.ci_lo:>5.2f},{w.ci_hi:>5.2f}]"
              f"{r.b_teaching:>8.2f} [{t.ci_lo:>5.2f},{t.ci_hi:>5.2f}]"
              f"{r.r2:>8.2f}")
    print("\n  Brackets are 95% bootstrap intervals (1000 resamples).")
    zero = ci[(ci.model == "oce") & (ci.param == "workload") & ~ci.excludes_zero]
    print(f"  Workload intervals containing zero: {len(zero)} of 3")
    print(f"  Teaching intervals containing zero: "
          f"{len(ci[(ci.model=='oce') & (ci.param=='teaching') & ~ci.excludes_zero])} of 3")
    print("\n  Read: teaching quality carries the rating; workload does not move it.")

    rule("Q1c  DOES COURSETABLE TELL THE SAME STORY?")
    side = oce[["discipline", "r2"]].merge(ct[["discipline", "r2"]], on="discipline",
                                           suffixes=("_oce", "_ct"))
    for _, r in side.iterrows():
        print(f"  {LABEL[r.discipline]:<17} R^2 from evaluations {r.r2_oce:.2f}"
              f"   from CourseTable {r.r2_ct:.2f}")
    print(f"\n  CourseTable workload vs OCE workload      r = {metric('corr_workload_oce_vs_ct'):.2f}")
    print(f"  CourseTable rating   vs OCE overall       r = {metric('corr_overall_oce_vs_ct_rating'):.2f}")
    print(f"\n  Circularity test -- CourseTable's professor rating against:")
    print(f"    the OCE overall-course question         r = {metric('corr_ct_professor_vs_oce_overall'):.2f}")
    print(f"    the OCE teaching questions              r = {metric('corr_ct_professor_vs_oce_teaching'):.2f}")
    print("  A large gap would mean the professor score is the course rating relabelled.")

    rule("Q2  HIDDEN GEMS")
    g = gems[gems.model == "oce"]
    over = (g.residual_std > 2).sum()
    print(f"  Courses above the standardized-residual threshold of 2: {over}")
    print(f"  Reported under the top-5% fallback instead:\n")
    print(f"  {'course':<12}{'discipline':<18}{'size':<10}{'rating':>8}{'resid':>8}")
    for _, r in g.iterrows():
        print(f"  {r.course_code:<12}{LABEL[r.discipline]:<18}{r.size_bin:<10}"
              f"{r.actual_raw:>8.2f}{r.residual_std:>8.2f}")
    ctg = set(gems[gems.model == "coursetable"].course_code)
    print(f"\n  Same rule on CourseTable flags: {', '.join(sorted(ctg))}")
    print(f"  Overlap with the list above: {int(metric('gems_shared'))} courses")

    rule("ROBUSTNESS AND NUMERICAL CHECKS")
    print("  Adding Q7 (intellectual challenge) as a third predictor:")
    for _, r in rob.iterrows():
        print(f"    {LABEL[r.discipline]:<17} workload {r.b_workload:>6.2f}"
              f"   teaching {r.b_teaching:>5.2f}   challenge {r.b_challenge:>6.2f}"
              f"   R^2 {r.r2:.2f}")
    allfits = pd.concat([oce, ct, rob])
    print(f"\n  max |A^T e| across every fit : {allfits.orth_check.max():.2e}  (should be ~1e-15)")
    print(f"  condition number kappa(A)    : {allfits.kappa_A.min():.2f} to {allfits.kappa_A.max():.2f}")
    print(f"  normal equations == SVD      : {bool(allfits.svd_match.all())}")
    print(f"  normal equations == lstsq    : {bool(allfits.lstsq_match.all())}")
    print(f"  normal equations == statsmodels: {bool(allfits.statsmodels_match.all())}")

    rule("WHERE TO LOOK NEXT")
    for path, what in [
        ("output/qc_report.txt", "the three data-quality checks"),
        ("report/figures/fig1_weights.png", "Q1: the weights, with error bars"),
        ("report/figures/fig2_actual_vs_predicted.png", "Q2: actual vs predicted, gems labelled"),
        ("report/figures/fig4_circularity.png", "Q1c: the circularity test"),
        ("report/figures/fig5_projection.png", "the projection diagram for the maths section"),
        ("data/processed/clean.csv", "one tidy row per course, the analysis input"),
    ]:
        mark = " " if Path(path).exists() else "  MISSING:"
        print(f" {mark} {path:<46} {what}")


if __name__ == "__main__":
    main()
