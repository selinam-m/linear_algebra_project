"""Draw the course sample per discipline, and lay out the OCE entry sheet."""

import argparse
import sys
from pathlib import Path
from zlib import crc32

import numpy as np
import pandas as pd

SHEET_COLS = ["course_code", "title", "professors", "entered_by",
              "q4_mean", "q5_mean", "q6_mean", "q7_mean", "q8_mean",
              "q4_sd", "q5_sd", "q6_sd", "q7_sd", "q8_sd", "notes"]


def has_entries(path):
    if not path.exists():
        return False
    df = pd.read_csv(path, dtype=str).fillna("")
    if df.empty or "course_code" not in df:
        return False
    filled = [c for c in df.columns if c.startswith(("q4", "q5", "q6", "q7", "q8"))]
    return bool(len(filled) and (df[filled] != "").any().any())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frame", default="data/processed/frame.csv")
    ap.add_argument("--n", type=int, default=25, help="courses to sample per discipline")
    ap.add_argument("--backups", type=int, default=10)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="data/sampling/sampled.csv")
    ap.add_argument("--sheet", default="data/raw/oce_entries.csv")
    args = ap.parse_args()

    frame = Path(args.frame)
    if not frame.exists():
        sys.exit(f"{frame} not found -- run src/coursetable.py first")
    df = pd.read_csv(frame)

    picks = []
    for discipline in sorted(df["discipline"].unique()):
        pool = df[df["discipline"] == discipline].sort_values("course_code").reset_index(drop=True)
        want = args.n + args.backups
        if len(pool) < want:
            print(f"  warning: {discipline} has {len(pool)} eligible, wanted {want}")

        # Seed per discipline so a change to one never reshuffles the others.
        rng = np.random.default_rng([args.seed, crc32(discipline.encode())])
        order = rng.permutation(len(pool))[:want]

        chosen = pool.loc[order].copy()
        chosen["role"] = ["sample"] * min(args.n, len(order)) + \
                         ["backup"] * max(0, len(order) - args.n)
        chosen["order"] = range(1, len(chosen) + 1)
        picks.append(chosen)
        print(f"  {discipline:<16} {len(pool):>4} eligible -> "
              f"{min(args.n, len(order))} sampled, {max(0, len(order) - args.n)} backups")

    sampled = pd.concat(picks, ignore_index=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sampled.to_csv(out, index=False)
    print(f"\nwrote {out} ({len(sampled)} rows), seed {args.seed}")

    sheet = Path(args.sheet)
    if has_entries(sheet):
        print(f"\n{sheet} already has data -- left untouched.")
        return

    blank = sampled[sampled["role"] == "sample"][["course_code", "title", "professors"]].copy()
    for col in SHEET_COLS:
        if col not in blank.columns:
            blank[col] = ""
    sheet.parent.mkdir(parents=True, exist_ok=True)
    blank[SHEET_COLS].to_csv(sheet, index=False)
    print(f"wrote {sheet} with {len(blank)} courses to fill in")


if __name__ == "__main__":
    main()
