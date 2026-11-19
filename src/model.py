"""Least squares by the normal equations, with SVD and library cross-checks."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

DISCIPLINES = ["humanities", "social_sciences", "stem"]


def standardize(v):
    v = np.asarray(v, dtype=float)
    return (v - v.mean()) / v.std(ddof=1)


def fit_ls(X, y):
    """X: (n, p) predictors, y: (n,) response. Intercept added here."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    n = len(y)
    A = np.column_stack([np.ones(n), X])

    beta = np.linalg.solve(A.T @ A, A.T @ y)
    y_hat = A @ beta
    e = y - y_hat

    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    beta_svd = Vt.T @ np.diag(1 / s) @ U.T @ y

    beta_lstsq = np.linalg.lstsq(A, y, rcond=None)[0]
    beta_sm = sm.OLS(y, A).fit().params

    ss_tot = np.sum((y - y.mean()) ** 2)
    return {
        "beta": beta,
        "r2": 1 - (e @ e) / ss_tot,
        "residuals": e,
        "y_hat": y_hat,
        "A": A,
        "n": n,
        "sigma": np.sqrt((e @ e) / (n - A.shape[1])),
        "orth_check": np.max(np.abs(A.T @ e)),
        "kappa_A": s.max() / s.min(),
        "kappa_AtA": (s.max() / s.min()) ** 2,
        "singular_values": s,
        "svd_match": bool(np.allclose(beta, beta_svd)),
        "lstsq_match": bool(np.allclose(beta, beta_lstsq)),
        "statsmodels_match": bool(np.allclose(beta, beta_sm)),
    }


def load_clean(path="data/processed/clean.csv"):
    df = pd.read_csv(path)
    df["discipline"] = df["discipline"].str.strip().str.lower()
    return df


def fit_by_discipline(df, ycol, xcols, label):
    """Standardize within each discipline, then fit. Returns one row per discipline."""
    rows = []
    for discipline in DISCIPLINES:
        sub = df[df["discipline"] == discipline].dropna(subset=[ycol] + xcols)
        if len(sub) < len(xcols) + 3:
            print(f"  skipping {label}/{discipline}: only {len(sub)} usable courses")
            continue

        y = standardize(sub[ycol])
        X = np.column_stack([standardize(sub[c]) for c in xcols])
        fit = fit_ls(X, y)

        row = {"model": label, "discipline": discipline, "n": fit["n"], "b0": fit["beta"][0]}
        for j, c in enumerate(xcols):
            row[f"b_{c}"] = fit["beta"][j + 1]
        row.update({
            "r2": fit["r2"],
            "corr_x1_x2": float(np.corrcoef(X[:, 0], X[:, 1])[0, 1]),
            "kappa_A": fit["kappa_A"],
            "kappa_AtA": fit["kappa_AtA"],
            "orth_check": fit["orth_check"],
            "svd_match": fit["svd_match"],
            "lstsq_match": fit["lstsq_match"],
            "statsmodels_match": fit["statsmodels_match"],
        })
        rows.append(row)
    return pd.DataFrame(rows)


def pooled_design(df, ycol, xcols, baseline="stem"):
    """Pooled fit with discipline dummies. One level is dropped to keep A full rank."""
    sub = df.dropna(subset=[ycol] + xcols).copy()

    parts = []
    names = []
    for c in xcols:
        std = sub.groupby("discipline")[c].transform(lambda v: (v - v.mean()) / v.std(ddof=1))
        parts.append(std.to_numpy())
        names.append(c)

    present = [d for d in DISCIPLINES if d in set(sub["discipline"]) and d != baseline]
    for d in present:
        parts.append((sub["discipline"] == d).astype(float).to_numpy())
        names.append(f"is_{d}")

    y = sub.groupby("discipline")[ycol].transform(lambda v: (v - v.mean()) / v.std(ddof=1)).to_numpy()
    return sub.reset_index(drop=True), np.column_stack(parts), y, names


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clean", default="data/processed/clean.csv")
    args = ap.parse_args()

    df = load_clean(args.clean)
    Path("output").mkdir(exist_ok=True)

    print("Model A (OCE):")
    oce = fit_by_discipline(df, "overall", ["workload", "teaching"], "oce")
    oce.to_csv("output/betas_oce.csv", index=False)
    print(oce.to_string(index=False) if not oce.empty else "  no fits")

    print("\nModel B (CourseTable):")
    ct = fit_by_discipline(df, "ct_rating", ["ct_workload", "ct_professor"], "coursetable")
    ct.to_csv("output/betas_ct.csv", index=False)
    print(ct.to_string(index=False) if not ct.empty else "  no fits")

    print("\nRobustness (OCE + intellectual challenge):")
    rb = fit_by_discipline(df, "overall", ["workload", "teaching", "challenge"], "oce_robust")
    rb.to_csv("output/betas_robust.csv", index=False)
    print(rb.to_string(index=False) if not rb.empty else "  no fits")

    print("\nwrote output/betas_oce.csv, output/betas_ct.csv, output/betas_robust.csv")


if __name__ == "__main__":
    main()
