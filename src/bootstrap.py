"""Bootstrap confidence intervals for the standardized weights."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from model import DISCIPLINES, fit_ls, load_clean, standardize

MODELS = {
    "oce": ("overall", ["workload", "teaching"]),
    "coursetable": ("ct_rating", ["ct_workload", "ct_professor"]),
}


def intervals(sub, ycol, xcols, reps, rng):
    y = standardize(sub[ycol])
    X = np.column_stack([standardize(sub[c]) for c in xcols])
    point = fit_ls(X, y)["beta"]

    n = len(y)
    draws = np.empty((reps, len(xcols) + 1))
    for b in range(reps):
        idx = rng.integers(0, n, n)
        A = np.column_stack([np.ones(n), X[idx]])
        try:
            draws[b] = np.linalg.solve(A.T @ A, A.T @ y[idx])
        except np.linalg.LinAlgError:
            draws[b] = np.nan

    lo, hi = np.nanpercentile(draws, [2.5, 97.5], axis=0)
    return point, lo, hi


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clean", default="data/processed/clean.csv")
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    df = load_clean(args.clean)
    rng = np.random.default_rng(args.seed)
    rows = []

    for label, (ycol, xcols) in MODELS.items():
        for discipline in DISCIPLINES:
            sub = df[df["discipline"] == discipline].dropna(subset=[ycol] + xcols)
            if len(sub) < len(xcols) + 3:
                continue
            point, lo, hi = intervals(sub, ycol, xcols, args.reps, rng)
            for j, name in enumerate(["intercept"] + xcols):
                rows.append({
                    "model": label,
                    "discipline": discipline,
                    "param": name,
                    "estimate": point[j],
                    "ci_lo": lo[j],
                    "ci_hi": hi[j],
                    "excludes_zero": bool(lo[j] > 0 or hi[j] < 0),
                    "n": len(sub),
                    "reps": args.reps,
                })

    out = pd.DataFrame(rows)
    Path("output").mkdir(exist_ok=True)
    out.to_csv("output/beta_ci.csv", index=False)
    print(out[out["param"] != "intercept"].to_string(index=False))
    print(f"\nwrote output/beta_ci.csv ({args.reps} resamples, seed {args.seed})")


if __name__ == "__main__":
    main()
