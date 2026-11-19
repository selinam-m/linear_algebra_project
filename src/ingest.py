"""Turn collected OCE pages into the entry sheet and the response-count file.

Each collected record holds, per question, the actual answer each respondent
gave. Means and standard deviations are computed from those directly, so the
analysis is not limited to the one-decimal figures OCE prints.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

QUESTIONS = ["4", "5", "6", "7", "8"]

SCALES = {
    "4": ["poor", "fair", "good", "very good", "excellent"],
    "5": ["strongly disagree", "disagree", "neutral", "agree", "strongly agree"],
    "6": ["strongly disagree", "disagree", "neutral", "agree", "strongly agree"],
    "7": ["much less", "less", "same", "greater", "much greater"],
    "8": ["much less", "less", "same", "greater", "much greater"],
}


def counts_of(answers, q):
    """Answer words to counts over 1-5. Raises on anything unrecognised."""
    scale = SCALES[q]
    counts = [0] * 5
    for word, n in answers.items():
        if word not in scale:
            raise ValueError(f"Q{q}: unrecognised answer {word!r}")
        counts[scale.index(word)] += n
    return counts


def mean_sd(counts):
    n = sum(counts)
    if n == 0:
        return None, None, 0
    mean = sum((k + 1) * c for k, c in enumerate(counts)) / n
    if n == 1:
        return mean, 0.0, n
    var = sum(c * ((k + 1) - mean) ** 2 for k, c in enumerate(counts)) / (n - 1)
    return mean, math.sqrt(var), n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collected", default="data/raw/collected")
    ap.add_argument("--sheet", default="data/raw/oce_entries.csv")
    ap.add_argument("--qc-counts", default="data/raw/qc_counts.csv")
    ap.add_argument("--displayed", default="data/raw/displayed.csv")
    args = ap.parse_args()

    files = sorted(Path(args.collected).glob("*.json"))
    if not files:
        sys.exit(f"no collected files in {args.collected}")

    records = {}
    for path in files:
        for rec in json.loads(path.read_text(encoding="utf-8")):
            if rec.get("err") and rec["code"] in records:
                continue
            records[rec["code"]] = rec

    rows, count_rows, disp_rows, problems = [], [], [], []
    for code, rec in sorted(records.items()):
        if rec.get("err"):
            problems.append(f"{code}: {rec['err']}")
            continue

        row = {"course_code": code, "entered_by": "oce",
               "oce_division": rec.get("division"),
               "oce_enrolled": rec.get("enrolled"),
               "oce_responded": rec.get("responded")}
        counts_row = {"course_code": code, "entered_by": "oce"}
        disp_row = {"course_code": code}
        usable = True

        for q in QUESTIONS:
            answers = rec.get("ans", {}).get(f"YC40{q}") or {}
            if not answers or "err" in answers:
                problems.append(f"{code}: no response data for Q{q}")
                usable = False
                break
            try:
                counts = counts_of(answers, q)
            except ValueError as exc:
                problems.append(f"{code}: {exc}")
                usable = False
                break

            mean, sd, n = mean_sd(counts)
            row[f"q{q}_mean"] = round(mean, 4)
            row[f"q{q}_sd"] = round(sd, 4)
            row[f"q{q}_n"] = n
            for k in range(5):
                counts_row[f"q{q}_{k + 1}"] = counts[k]
            disp_row[f"q{q}_disp"] = rec.get("disp", {}).get(q)

        if usable:
            rows.append(row)
            count_rows.append(counts_row)
            disp_rows.append(disp_row)

    if not rows:
        sys.exit("nothing usable collected")

    collected = pd.DataFrame(rows).set_index("course_code")

    sheet = pd.read_csv(args.sheet)
    sheet["course_code"] = sheet["course_code"].astype(str).str.strip().str.upper()
    for col in collected.columns:
        if col not in sheet.columns:
            sheet[col] = pd.NA
    for col in ["entered_by", "oce_division", "notes", "title", "professors"]:
        if col in sheet.columns:
            sheet[col] = sheet[col].astype("object")

    indexed = sheet.set_index("course_code")
    missing = [c for c in indexed.index if c not in collected.index]
    for code in collected.index:
        if code not in indexed.index:
            problems.append(f"{code}: collected but not in the sheet")
            continue
        for col, value in collected.loc[code].items():
            indexed.loc[code, col] = value

    indexed.reset_index().to_csv(args.sheet, index=False)
    pd.DataFrame(count_rows).to_csv(args.qc_counts, index=False)
    pd.DataFrame(disp_rows).to_csv(args.displayed, index=False)

    print(f"collected files: {len(files)}, courses: {len(records)}")
    print(f"written to the sheet: {len(rows)}")
    print(f"response counts:     {args.qc_counts}")
    print(f"displayed figures:   {args.displayed}")
    if missing:
        print(f"\nsampled but not collected ({len(missing)}): {', '.join(missing)}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
