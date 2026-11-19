"""Generate a clearly-labelled fake frame and entry sheet, so the pipeline can be
tested before real collection finishes.

NOTHING from this file may appear in the report or slides. Course codes are
prefixed TST so a stray row is obvious. The real run reads data/raw/ and the
frame built from CourseTable's export.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DISCIPLINES = ["humanities", "social_sciences", "stem"]
# The STEM code carries an ampersand on purpose: real subjects include MB&B,
# EP&E and S&DS, and those must survive the LaTeX tables.
SUBJECT = {"humanities": "TSTH", "social_sciences": "TSTS", "stem": "TS&E"}
AREA = {"humanities": "Hu", "social_sciences": "So", "stem": "Sc"}

# True weights the fake data is built from, so the fit has something to recover.
TRUTH = {
    "humanities": {"workload": -0.15, "teaching": 0.70},
    "social_sciences": {"workload": -0.30, "teaching": 0.60},
    "stem": {"workload": -0.45, "teaching": 0.50},
}

SHEET_COLS = ["course_code", "title", "professors", "entered_by",
              "q4_mean", "q5_mean", "q6_mean", "q7_mean", "q8_mean",
              "q4_sd", "q5_sd", "q6_sd", "q7_sd", "q8_sd", "notes"]


def counts_for_mean(rng, target, n, spread=0.9):
    k = np.arange(1, 6)
    p = np.exp(-((k - target) ** 2) / (2 * spread ** 2))
    p /= p.sum()
    return rng.multinomial(n, p)


def mean_of(counts):
    k = np.arange(1, 6)
    return float((k * counts).sum() / counts.sum())


def sd_of(counts):
    k = np.arange(1, 6)
    n = counts.sum()
    m = (k * counts).sum() / n
    return float(np.sqrt((counts * (k - m) ** 2).sum() / max(n - 1, 1)))


def main():
    ap = argparse.ArgumentParser(description="Build fake test data.")
    ap.add_argument("--per-discipline", type=int, default=25)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--qc", type=int, default=15)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    frame_rows, sheet_rows, count_rows = [], [], []

    for discipline in DISCIPLINES:
        for i in range(args.per_discipline):
            n_resp = int(rng.integers(8, 90))
            enrollment = int(n_resp * rng.uniform(1.4, 2.6))

            workload_t = np.clip(rng.normal(3.1, 0.55), 1.2, 4.9)
            teaching_t = np.clip(rng.normal(4.0, 0.45), 1.5, 5.0)
            challenge_t = np.clip(0.6 * workload_t + rng.normal(1.3, 0.4), 1.2, 5.0)

            w = TRUTH[discipline]
            overall_t = (3.9
                         + w["workload"] * (workload_t - 3.1)
                         + w["teaching"] * (teaching_t - 4.0)
                         + rng.normal(0, 0.22))
            # A few deliberate outliers so the gem rule has something to catch.
            if rng.random() < 0.05:
                overall_t += rng.uniform(0.6, 0.9)
            overall_t = float(np.clip(overall_t, 1.0, 5.0))

            q5_t = np.clip(teaching_t + rng.normal(0, 0.18), 1.0, 5.0)
            q6_t = np.clip(2 * teaching_t - q5_t, 1.0, 5.0)

            counts = {p: counts_for_mean(rng, t, n_resp)
                      for p, t in [("q4", overall_t), ("q5", q5_t), ("q6", q6_t),
                                   ("q7", challenge_t), ("q8", workload_t)]}
            means = {p: round(mean_of(c), 2) for p, c in counts.items()}
            sds = {p: round(sd_of(c), 1) for p, c in counts.items()}

            code = f"{SUBJECT[discipline]} {1000 + i}"
            title = f"Test Course {i} ({discipline})"
            prof = f"Test Professor {i % 11}"

            # CourseTable's figures are historical, so they only loosely track
            # this term's evaluations.
            ct_rating = round(np.clip(means["q4"] + rng.normal(0, 0.35), 1, 5), 3)
            ct_workload = round(np.clip(means["q8"] + rng.normal(0, 0.35), 1, 5), 3)
            ct_professor = round(np.clip(0.7 * ct_rating + 0.3 * means["q5"]
                                         + rng.normal(0, 0.2), 1, 5), 3)

            frame_rows.append({
                "course_code": code, "subject": SUBJECT[discipline], "number": 1000 + i,
                "title": title, "discipline": discipline, "professors": prof,
                "enrollment": enrollment, "n_responses": n_resp,
                "ct_rating": ct_rating, "ct_professor": ct_professor,
                "ct_workload": ct_workload, "ct_scope": "all-time",
                "areas": AREA[discipline], "course_id": 900000 + len(frame_rows),
            })
            sheet_rows.append({
                "course_code": code, "title": title, "professors": prof,
                "entered_by": "test",
                **{f"{p}_mean": means[p] for p in counts},
                **{f"{p}_sd": sds[p] for p in counts},
                "notes": "FAKE",
            })
            count_rows.append({"course_code": code, "entered_by": "test",
                               **{f"{p}_{k}": int(counts[p][k - 1])
                                  for p in counts for k in range(1, 6)}})

    frame = pd.DataFrame(frame_rows)
    sheet = pd.DataFrame(sheet_rows)[SHEET_COLS]
    counts_df = pd.DataFrame(count_rows)

    # Three rows clean.py should reject, for different reasons.
    frame.loc[len(frame)] = {**frame_rows[0], "course_code": "TSTH 9000",
                             "n_responses": 3, "course_id": 999001}
    sheet.loc[len(sheet)] = {**sheet_rows[0], "course_code": "TSTH 9000",
                             "notes": "FAKE too few responses"}
    sheet.loc[len(sheet)] = {**sheet_rows[1], "course_code": "TSTH 9001",
                             "q4_mean": 7.4, "notes": "FAKE out of range"}
    frame.loc[len(frame)] = {**frame_rows[1], "course_code": "TSTH 9001",
                             "course_id": 999002}
    sheet.loc[len(sheet)] = {**sheet_rows[2], "course_code": "TSTX 9002",
                             "notes": "FAKE not in frame"}

    # What OCE would have displayed: our means rounded to one decimal.
    displayed = pd.DataFrame({"course_code": sheet["course_code"]})
    for q in ["q4", "q5", "q6", "q7", "q8"]:
        displayed[f"{q}_disp"] = (sheet[f"{q}_mean"].round(1).map("{:.1f}".format)
                                  + "±" + sheet[f"{q}_sd"].round(1).map("{:.1f}".format))

    Path("data/test").mkdir(parents=True, exist_ok=True)
    frame.to_csv("data/test/fake_frame.csv", index=False)
    sheet.to_csv("data/test/fake_entries.csv", index=False)
    counts_df.to_csv("data/test/fake_qc_counts.csv", index=False)
    displayed.to_csv("data/test/fake_displayed.csv", index=False)
    print(f"wrote data/test/fake_frame.csv ({len(frame)} courses)")
    print(f"wrote data/test/fake_entries.csv ({len(sheet)} rows, 3 deliberately bad)")
    print(f"wrote data/test/fake_qc_counts.csv ({len(counts_df)} rows)")
    print(f"wrote data/test/fake_displayed.csv ({len(displayed)} rows)")


if __name__ == "__main__":
    main()
