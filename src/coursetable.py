"""Build the eligible-course frame from CourseTable's Fall 2025 export.

Two files, both keyed by course_id: one carries the ratings, the other the
catalogue. Reads them as plain data and writes one table of courses that are
eligible to be sampled.
"""

import argparse
import json
from pathlib import Path

import pandas as pd

# Yale's own distributional areas.
AREA = {"Hu": "humanities", "So": "social_sciences", "Sc": "stem"}

# Math and computer science carry no area tag; Yale files them under the QR
# skill instead. QR on its own is no use as a marker because ECON carries it too,
# so these subjects are named explicitly.
STEM_SUBJECTS = {"MATH", "CPSC", "S&DS", "ENAS", "AMTH"}

MIN_RESPONSES = 8


def discipline_of(areas, primary_subject):
    """Area tag decides. Only an untagged course falls back to the subject list,
    and only on its first-listed subject, so a cross-listing cannot drag it."""
    if len(areas) == 1 and areas[0] in AREA:
        return AREA[areas[0]]
    if not areas and primary_subject in STEM_SUBJECTS:
        return "stem"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ratings", default="data/coursetable/202503.json")
    ap.add_argument("--catalogue", default="data/coursetable/202503_public data.json")
    ap.add_argument("--out", default="data/processed/frame.csv")
    ap.add_argument("--require-professor", action="store_true", default=True)
    args = ap.parse_args()

    with open(args.ratings, encoding="utf-8") as f:
        ratings = {x["course_id"]: x for x in json.load(f)}
    with open(args.catalogue, encoding="utf-8") as f:
        catalogue = json.load(f)

    rows = []
    skipped = {"no YC listing": 0, "no single discipline": 0, "too few responses": 0,
               "missing CourseTable rating": 0, "missing professor rating": 0}

    for course in catalogue:
        yc = [l for l in (course.get("listings") or []) if l.get("school") == "YC"]
        if not yc:
            skipped["no YC listing"] += 1
            continue

        # Cross-listed courses take the first listed subject.
        primary = yc[0]
        areas = sorted(course.get("areas") or [])
        discipline = discipline_of(areas, primary["subject"])
        if discipline is None:
            skipped["no single discipline"] += 1
            continue

        rec = ratings.get(course["course_id"], {})
        stat = rec.get("evaluation_statistic") or {}
        n_responses = stat.get("responses")
        if not n_responses or n_responses < MIN_RESPONSES:
            skipped["too few responses"] += 1
            continue

        if rec.get("average_rating") is None or rec.get("average_workload") is None:
            skipped["missing CourseTable rating"] += 1
            continue
        if args.require_professor and rec.get("average_professor_rating") is None:
            skipped["missing professor rating"] += 1
            continue

        profs = "; ".join(p["professor"]["name"]
                          for p in (course.get("course_professors") or [])
                          if p.get("professor"))

        rows.append({
            "course_code": primary["course_code"],
            "crn": primary.get("crn"),
            "subject": primary["subject"],
            "number": primary["number"],
            "title": course.get("title", ""),
            "discipline": discipline,
            "professors": profs,
            "enrollment": stat.get("enrolled"),
            "n_responses": n_responses,
            "ct_rating": rec["average_rating"],
            "ct_professor": rec.get("average_professor_rating"),
            "ct_workload": rec["average_workload"],
            "ct_scope": "all-time",
            "areas": ",".join(areas) if areas else "",
            "course_id": course["course_id"],
        })

    df = pd.DataFrame(rows)

    # Several sections can share a course code; keep the best-answered one.
    before = len(df)
    df = (df.sort_values("n_responses", ascending=False)
            .drop_duplicates(subset="course_code", keep="first")
            .sort_values(["discipline", "course_code"])
            .reset_index(drop=True))
    merged_sections = before - len(df)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    print(f"catalogue records: {len(catalogue)}")
    for reason, n in skipped.items():
        print(f"  skipped, {reason}: {n}")
    print(f"  duplicate sections merged: {merged_sections}")
    print()
    for discipline, n in df["discipline"].value_counts().sort_index().items():
        tagged = (df[df["discipline"] == discipline]["areas"] != "").sum()
        print(f"  {discipline:<16} {n:>4} eligible  ({n - tagged} added by subject, not area tag)")
    print(f"\nwrote {out} ({len(df)} courses)")


if __name__ == "__main__":
    main()
