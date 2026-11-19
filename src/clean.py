"""Join the OCE entry sheet to the CourseTable frame, with a QC report.

The sheet carries only what has to be read off an OCE page. Discipline,
enrollment, response count, title and the CourseTable columns all come from the
frame, so they cannot be mistyped.
"""

import argparse
from pathlib import Path

import pandas as pd

MEAN_COLS = ["q4_mean", "q5_mean", "q6_mean", "q7_mean", "q8_mean"]
SD_COLS = ["q4_sd", "q5_sd", "q6_sd", "q7_sd", "q8_sd"]
CT_COLS = ["ct_rating", "ct_professor", "ct_workload"]
MIN_RESPONSES = 8
MAX_SD = 2.1

RENAME = {"q4_mean": "overall", "q7_mean": "challenge", "q8_mean": "workload"}


def size_bin(enrollment):
    if pd.isna(enrollment):
        return "unknown"
    if enrollment < 20:
        return "seminar"
    if enrollment < 80:
        return "mid"
    return "lecture"


def displayed_check(entries, path, lines):
    """Our means come from response-level data; OCE prints them rounded to one
    decimal. Every computed value should sit within half a rounding step."""
    if not path.exists():
        lines.append("Displayed-value check: no displayed.csv, skipped.")
        return
    disp = pd.read_csv(path)
    if disp.empty:
        lines.append("Displayed-value check: no data.")
        return
    disp["course_code"] = disp["course_code"].astype(str).str.strip().str.upper()

    merged = entries.merge(disp, on="course_code")
    compared = off = 0
    worst = 0.0
    for q in ["4", "5", "6", "7", "8"]:
        col, dcol = f"q{q}_mean", f"q{q}_disp"
        if dcol not in merged:
            continue
        ours = pd.to_numeric(merged[col], errors="coerce")
        theirs = pd.to_numeric(merged[dcol].astype(str).str.split("±").str[0], errors="coerce")
        both = ours.notna() & theirs.notna()
        diff = (ours - theirs).abs()
        compared += int(both.sum())
        if both.any():
            worst = max(worst, float(diff[both].max()))
        for i in merged.index[both & (diff > 0.051)]:
            off += 1
            lines.append(f"  {merged.loc[i, 'course_code']} Q{q}: computed {ours[i]:.3f}, "
                         f"OCE displays {theirs[i]}")

    lines.append(f"Computed means against the figures OCE displays:")
    lines.append(f"  values compared: {compared}")
    lines.append(f"  largest difference: {worst:.4f}  (0.05 is the rounding bound)")
    lines.append(f"  outside the rounding bound: {off}")


OCE_DIVISION = {"Humanities": "humanities",
                "Social Sciences": "social_sciences",
                "Sciences": "stem"}


def source_check(df, lines):
    """Two independent agreement checks between OCE and the CourseTable frame."""
    if "oce_responded" in df:
        ours = pd.to_numeric(df["n_responses"], errors="coerce")
        theirs = pd.to_numeric(df["oce_responded"], errors="coerce")
        both = ours.notna() & theirs.notna()
        exact = int((ours[both] == theirs[both]).sum())
        lines.append(f"Response counts, CourseTable against OCE: "
                     f"{exact}/{int(both.sum())} identical")
        for i in df.index[both & (ours != theirs)]:
            lines.append(f"  {df.loc[i, 'course_code']}: frame {ours[i]:.0f}, OCE {theirs[i]:.0f}")

    if "oce_division" in df:
        mapped = df["oce_division"].map(OCE_DIVISION)
        comparable = mapped.notna()
        agree = int((mapped[comparable] == df.loc[comparable, "discipline"]).sum())
        lines.append(f"\nDiscipline, our area tags against OCE's primary division: "
                     f"{agree}/{int(comparable.sum())} agree "
                     f"({int((~comparable).sum())} not comparable)")
        for i in df.index[comparable & (mapped != df["discipline"])]:
            lines.append(f"  {df.loc[i, 'course_code']}: OCE says {df.loc[i, 'oce_division']}, "
                         f"area tag says {df.loc[i, 'discipline']}")
        for i in df.index[~comparable]:
            lines.append(f"  {df.loc[i, 'course_code']}: OCE division "
                         f"{df.loc[i, 'oce_division']!r} has no equivalent")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entries", default="data/raw/oce_entries.csv")
    ap.add_argument("--frame", default="data/processed/frame.csv")
    ap.add_argument("--displayed", default="data/raw/displayed.csv")
    ap.add_argument("--out", default="data/processed/clean.csv")
    args = ap.parse_args()

    entries = pd.read_csv(args.entries)
    entries = entries[entries["course_code"].notna()].copy()
    entries["course_code"] = entries["course_code"].astype(str).str.strip().str.upper()
    entries = entries.drop(columns=[c for c in ["title", "professors"] if c in entries])

    frame = pd.read_csv(args.frame)
    frame["course_code"] = frame["course_code"].astype(str).str.strip().str.upper()

    merged = entries.merge(frame, on="course_code", how="left", indicator=True)

    dropped = []
    for i in merged.index[merged["_merge"] == "left_only"]:
        dropped.append({"course_code": merged.loc[i, "course_code"],
                        "reason": "not in the CourseTable frame"})

    for col in MEAN_COLS + SD_COLS:
        if col not in merged.columns:
            merged[col] = pd.NA
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    dup = merged.duplicated(subset=["course_code"], keep="first")
    for i in merged.index[dup]:
        dropped.append({"course_code": merged.loc[i, "course_code"], "reason": "duplicate row"})
    merged = merged[~dup]

    for i in merged.index:
        if merged.loc[i, "_merge"] == "left_only":
            continue
        reasons = []
        missing = [c for c in MEAN_COLS if pd.isna(merged.loc[i, c])]
        if missing:
            reasons.append("missing " + ",".join(missing))
        out_of_range = [c for c in MEAN_COLS
                        if pd.notna(merged.loc[i, c]) and not 1 <= merged.loc[i, c] <= 5]
        if out_of_range:
            reasons.append("out of [1,5]: " + ",".join(out_of_range))
        bad_sd = [c for c in SD_COLS
                  if pd.notna(merged.loc[i, c]) and not 0 <= merged.loc[i, c] <= MAX_SD]
        if bad_sd:
            reasons.append(f"sd outside [0,{MAX_SD}]: " + ",".join(bad_sd))
        if merged.loc[i, "n_responses"] < MIN_RESPONSES:
            reasons.append(f"n_responses < {MIN_RESPONSES}")
        if reasons:
            dropped.append({"course_code": merged.loc[i, "course_code"],
                            "reason": "; ".join(reasons)})

    drop_codes = {d["course_code"] for d in dropped}
    kept = merged[(merged["_merge"] == "both") & ~merged["course_code"].isin(drop_codes)].copy()
    qc_source = kept.copy()

    kept["teaching"] = kept[["q5_mean", "q6_mean"]].mean(axis=1)
    kept = kept.rename(columns=RENAME)
    kept["size_bin"] = kept["enrollment"].apply(size_bin)

    cols = ["course_code", "title", "subject", "discipline", "professors", "enrollment",
            "n_responses", "size_bin", "overall", "workload", "teaching", "challenge",
            "q5_mean", "q6_mean", *SD_COLS, "oce_division", "oce_responded",
            *CT_COLS, "ct_scope", "areas"]
    clean = kept[[c for c in cols if c in kept.columns]]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    clean.to_csv(args.out, index=False)
    pd.DataFrame(dropped, columns=["course_code", "reason"]).to_csv(
        "output/dropped_courses.csv", index=False)

    lines = ["QC report", "=" * 40, ""]
    lines.append(f"Rows in the entry sheet: {len(entries)}")
    lines.append(f"Courses kept:            {len(clean)}")
    lines.append(f"Courses dropped:         {len(dropped)}  (see output/dropped_courses.csv)")
    lines.append("")
    lines.append("Per discipline:")
    for discipline, n in clean["discipline"].value_counts().sort_index().items():
        lines.append(f"  {discipline:<16} {n}")
    lines.append("")
    sd_present = clean[SD_COLS].notna().all(axis=1).sum()
    lines.append(f"Courses with all five standard deviations: {sd_present}/{len(clean)}")
    lines.append(f"CourseTable columns come from the export, scope: "
                 f"{clean['ct_scope'].dropna().unique().tolist()}")
    lines.append("")
    displayed_check(qc_source, Path(args.displayed), lines)
    lines.append("")
    source_check(kept.reset_index(drop=True), lines)

    Path("output/qc_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {args.out} and output/qc_report.txt")


if __name__ == "__main__":
    main()
