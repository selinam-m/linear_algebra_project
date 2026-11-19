"""Turn the output tables into LaTeX fragments the report can \\input."""

import argparse
from pathlib import Path

import pandas as pd

OUT = Path("output")

LABEL = {"humanities": "Humanities", "social_sciences": "Social Sciences", "stem": "STEM"}

# Course codes carry ampersands (MB&B, EP&E, S&DS), which would otherwise end a
# table column. Headers are written by hand and keep their math.
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
           "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
           ">": r"\textgreater{}", "<": r"\textless{}"}


def escape_cells(df):
    df = df.copy()
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].map(lambda v: "".join(SPECIAL.get(c, c) for c in str(v)))
    return df


def write(df, name, caption, label, float_format="%.2f"):
    body = escape_cells(df).to_latex(index=False, escape=False, float_format=float_format,
                       column_format="l" * 1 + "r" * (len(df.columns) - 1))
    tex = (f"\\begin{{table}}[h]\n  \\centering\n  \\caption{{{caption}}}\n"
           f"  \\label{{{label}}}\n{body}\\end{{table}}\n")
    (OUT / name).write_text(tex, encoding="utf-8")
    print(f"  output/{name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()

    OUT.mkdir(exist_ok=True)
    print("tables:")

    oce = pd.read_csv(OUT / "betas_oce.csv")
    betas = oce[["discipline", "n", "b_workload", "b_teaching", "r2", "corr_x1_x2", "kappa_A"]].copy()
    betas["discipline"] = betas["discipline"].map(LABEL)
    betas.columns = ["Discipline", "$n$", r"$\hat\beta_{\text{workload}}$",
                     r"$\hat\beta_{\text{teaching}}$", "$R^2$", r"$r(x_1,x_2)$", r"$\kappa(A)$"]
    write(betas, "table_betas.tex",
          "Standardized least-squares weights from the evaluation data, by discipline.",
          "tab:betas")

    ct = pd.read_csv(OUT / "betas_ct.csv")
    side = oce[["discipline", "b_workload", "b_teaching", "r2"]].merge(
        ct[["discipline", "b_ct_workload", "b_ct_professor", "r2"]],
        on="discipline", suffixes=("_oce", "_ct"))
    side["discipline"] = side["discipline"].map(LABEL)
    side.columns = ["Discipline", "Workload (OCE)", "Teaching (OCE)", "$R^2$ (OCE)",
                    "Workload (CT)", "Professor (CT)", "$R^2$ (CT)"]
    write(side, "table_compare.tex",
          "The same model fitted to the evaluation data and to CourseTable's summary figures.",
          "tab:compare")

    gems = pd.read_csv(OUT / "gems.csv")
    gems = gems[gems["model"] == "oce"][
        ["course_code", "discipline", "size_bin", "actual_raw", "predicted_std",
         "residual_std", "rule"]].copy()
    gems["discipline"] = gems["discipline"].map(LABEL)
    gems.columns = ["Course", "Discipline", "Class size", "Actual",
                    "Predicted (std.)", "$r_i$", "Rule"]
    write(gems, "table_gems.tex", "Courses flagged as hidden gems.", "tab:gems")

    ci = pd.read_csv(OUT / "beta_ci.csv")
    ci = ci[(ci["model"] == "oce") & (ci["param"] != "intercept")][
        ["discipline", "param", "estimate", "ci_lo", "ci_hi"]].copy()
    ci["discipline"] = ci["discipline"].map(LABEL)
    ci.columns = ["Discipline", "Predictor", "Estimate", "2.5\\%", "97.5\\%"]
    write(ci, "table_beta_ci.tex",
          "Bootstrap 95\\% intervals, 1000 resamples within each discipline.", "tab:ci")


if __name__ == "__main__":
    main()
