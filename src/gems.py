"""Find courses rated far above what workload and teaching quality predict."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from model import fit_ls, load_clean, pooled_design

MODELS = {
    "oce": ("overall", ["workload", "teaching"]),
    "coursetable": ("ct_rating", ["ct_workload", "ct_professor"]),
}


def find_gems(df, ycol, xcols, label, threshold, top_pct):
    sub, X, y, names = pooled_design(df, ycol, xcols)
    fit = fit_ls(X, y)
    r = fit["residuals"] / fit["sigma"]

    out = pd.DataFrame({
        "model": label,
        "course_code": sub["course_code"].to_numpy(),
        "title": sub["title"].to_numpy() if "title" in sub else "",
        "discipline": sub["discipline"].to_numpy(),
        "size_bin": sub["size_bin"].to_numpy(),
        "actual_std": y,
        "predicted_std": fit["y_hat"],
        "residual_std": r,
        "actual_raw": sub[ycol].to_numpy(),
    })

    over = out["residual_std"] > threshold
    out["rule"] = np.where(over, f"residual > {threshold}", "")

    # Fall back to the top slice if the hard threshold catches almost nothing.
    if over.sum() < 3:
        cutoff = out["residual_std"].quantile(1 - top_pct)
        also = (out["residual_std"] >= cutoff) & ~over
        out.loc[also, "rule"] = f"top {top_pct:.0%}"

    gems = out[out["rule"] != ""].sort_values("residual_std", ascending=False)
    print(f"{label}: {int(over.sum())} above residual {threshold}, "
          f"{len(gems)} flagged in total (n = {len(out)}, columns = {names})")
    return out, gems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clean", default="data/processed/clean.csv")
    ap.add_argument("--threshold", type=float, default=2.0)
    ap.add_argument("--top-pct", type=float, default=0.05)
    args = ap.parse_args()

    df = load_clean(args.clean)
    Path("output").mkdir(exist_ok=True)

    all_resid, all_gems = [], []
    for label, (ycol, xcols) in MODELS.items():
        if df.dropna(subset=[ycol] + xcols).empty:
            continue
        resid, gems = find_gems(df, ycol, xcols, label, args.threshold, args.top_pct)
        all_resid.append(resid)
        all_gems.append(gems)

    resid = pd.concat(all_resid, ignore_index=True)
    gems = pd.concat(all_gems, ignore_index=True)
    resid.to_csv("output/residuals.csv", index=False)
    gems.to_csv("output/gems.csv", index=False)

    oce = resid[resid["model"] == "oce"]
    flagged = set(gems[gems["model"] == "oce"]["course_code"])
    rows = []
    for key in ["discipline", "size_bin"]:
        for value, group in oce.groupby(key):
            rows.append({
                "grouping": key,
                "group": value,
                "courses": len(group),
                "gems": int(group["course_code"].isin(flagged).sum()),
                "gem_rate": group["course_code"].isin(flagged).mean(),
            })
    by_group = pd.DataFrame(rows)
    by_group.to_csv("output/gems_by_group.csv", index=False)

    print()
    print(by_group.to_string(index=False))
    print("\nwrote output/gems.csv, output/gems_by_group.csv, output/residuals.csv")


if __name__ == "__main__":
    main()
