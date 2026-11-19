"""Does CourseTable's summary data tell the same story as the raw evaluations?"""

import argparse
from pathlib import Path

import pandas as pd

from model import DISCIPLINES, load_clean


def corr(df, a, b):
    sub = df.dropna(subset=[a, b])
    if len(sub) < 3:
        return float("nan")
    return float(sub[a].corr(sub[b]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clean", default="data/processed/clean.csv")
    args = ap.parse_args()

    df = load_clean(args.clean)
    rows = []

    oce = pd.read_csv("output/betas_oce.csv")
    ct = pd.read_csv("output/betas_ct.csv")
    side = oce.merge(ct, on="discipline", suffixes=("_oce", "_ct"))
    for _, r in side.iterrows():
        rows += [
            {"metric": "beta_workload_oce", "discipline": r["discipline"], "value": r["b_workload"]},
            {"metric": "beta_workload_ct", "discipline": r["discipline"], "value": r["b_ct_workload"]},
            {"metric": "beta_teaching_oce", "discipline": r["discipline"], "value": r["b_teaching"]},
            {"metric": "beta_professor_ct", "discipline": r["discipline"], "value": r["b_ct_professor"]},
            {"metric": "r2_oce", "discipline": r["discipline"], "value": r["r2_oce"]},
            {"metric": "r2_ct", "discipline": r["discipline"], "value": r["r2_ct"]},
        ]

    scopes = [("all", df)] + [(d, df[df["discipline"] == d]) for d in DISCIPLINES]
    for scope, sub in scopes:
        rows += [
            {"metric": "corr_workload_oce_vs_ct", "discipline": scope,
             "value": corr(sub, "workload", "ct_workload")},
            {"metric": "corr_overall_oce_vs_ct_rating", "discipline": scope,
             "value": corr(sub, "overall", "ct_rating")},
            # Circularity test: does CourseTable's professor score track the overall
            # course question more closely than it tracks the teaching questions?
            {"metric": "corr_ct_professor_vs_oce_overall", "discipline": scope,
             "value": corr(sub, "ct_professor", "overall")},
            {"metric": "corr_ct_professor_vs_oce_teaching", "discipline": scope,
             "value": corr(sub, "ct_professor", "teaching")},
        ]

    gems_path = Path("output/gems.csv")
    if gems_path.exists():
        gems = pd.read_csv(gems_path)
        a = set(gems[gems["model"] == "oce"]["course_code"])
        b = set(gems[gems["model"] == "coursetable"]["course_code"])
        union = a | b
        rows += [
            {"metric": "gems_oce", "discipline": "all", "value": len(a)},
            {"metric": "gems_ct", "discipline": "all", "value": len(b)},
            {"metric": "gems_shared", "discipline": "all", "value": len(a & b)},
            {"metric": "gem_jaccard", "discipline": "all",
             "value": len(a & b) / len(union) if union else float("nan")},
        ]

    out = pd.DataFrame(rows)
    out.to_csv("output/compare.csv", index=False)

    print(side[["discipline", "b_workload", "b_ct_workload", "b_teaching",
                "b_ct_professor", "r2_oce", "r2_ct"]].to_string(index=False))
    print()
    print(out[out["metric"].str.startswith("corr_ct_professor")].to_string(index=False))
    print()
    print(out[out["metric"].str.startswith("gem")].to_string(index=False))
    print("\nwrote output/compare.csv")


if __name__ == "__main__":
    main()
