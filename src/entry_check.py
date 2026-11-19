"""Validate the entry sheet against the frame while collection is in progress."""

import argparse
import sys
from pathlib import Path

import pandas as pd

MEAN_COLS = ["q4_mean", "q5_mean", "q6_mean", "q7_mean", "q8_mean"]
SD_COLS = ["q4_sd", "q5_sd", "q6_sd", "q7_sd", "q8_sd"]
MAX_SD = 2.1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entries", default="data/raw/oce_entries.csv")
    ap.add_argument("--frame", default="data/processed/frame.csv")
    ap.add_argument("--target", type=int, default=25, help="courses wanted per discipline")
    args = ap.parse_args()

    path = Path(args.entries)
    if not path.exists():
        sys.exit(f"{path} not found -- run src/sample_courses.py to lay it out")

    df = pd.read_csv(path, dtype=str).fillna("")
    df = df[df["course_code"].str.strip() != ""].reset_index(drop=True)
    df["course_code"] = df["course_code"].str.strip().str.upper()
    if df.empty:
        print("sheet is empty -- nothing to check yet")
        return

    frame = pd.read_csv(args.frame)
    frame["course_code"] = frame["course_code"].astype(str).str.strip().str.upper()
    known = frame.set_index("course_code")["discipline"].to_dict()

    nums = df[MEAN_COLS + SD_COLS].apply(pd.to_numeric, errors="coerce")
    started = nums.notna().any(axis=1)

    problems = []
    for i, row in df.iterrows():
        code = row["course_code"]
        where = f"row {i + 2} ({code})"

        if code not in known:
            problems.append(f"{where}: not in the frame -- check the course code")
            continue
        if not started[i]:
            continue

        blank = [c for c in MEAN_COLS if pd.isna(nums.loc[i, c])]
        if blank:
            problems.append(f"{where}: part-filled, missing {', '.join(blank)}")

        bad = [c for c in MEAN_COLS if pd.notna(nums.loc[i, c]) and not 1 <= nums.loc[i, c] <= 5]
        if bad:
            problems.append(f"{where}: outside [1, 5] -> "
                            + ", ".join(f"{c}={nums.loc[i, c]}" for c in bad))

        # 2.0 is the largest standard deviation a 1-5 scale can produce.
        bad_sd = [c for c in SD_COLS
                  if pd.isna(nums.loc[i, c]) or not 0 <= nums.loc[i, c] <= MAX_SD]
        if bad_sd:
            problems.append(f"{where}: missing or implausible {', '.join(bad_sd)}")

        if row["entered_by"].strip() == "":
            problems.append(f"{where}: entered_by blank")

    for code in sorted(df[df.duplicated(subset=["course_code"], keep=False)]["course_code"].unique()):
        problems.append(f"duplicate course_code: {code}")

    done = df[started].copy()
    done["discipline"] = done["course_code"].map(known)

    print(f"{path}: {len(df)} courses listed, {len(done)} with numbers entered\n")
    for discipline in sorted(frame["discipline"].unique()):
        have = int((done["discipline"] == discipline).sum())
        print(f"  {discipline:<16} {have:>3}/{args.target}  {'#' * have}")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print("\nno problems found")


if __name__ == "__main__":
    main()
