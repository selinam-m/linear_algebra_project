"""Run the whole pipeline in order.

    python run_all.py           # real data
    python run_all.py --test    # fake data, for checking the code
"""

import argparse
import subprocess
import sys
from pathlib import Path

REAL = {
    "entries": "data/raw/oce_entries.csv",
    "frame": "data/processed/frame.csv",
    "displayed": "data/raw/displayed.csv",
}
TEST = {
    "entries": "data/test/fake_entries.csv",
    "frame": "data/test/fake_frame.csv",
    "displayed": "data/test/fake_displayed.csv",
}


def run(script, *extra, isolated=False):
    cmd = [sys.executable]
    if isolated:
        cmd.append("-I")
    cmd += [str(Path("src") / script), *extra]
    print("\n" + "=" * 70)
    print("$ " + " ".join(cmd[1:]))
    print("=" * 70)
    if subprocess.run(cmd).returncode != 0:
        sys.exit(f"\n{script} failed")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", action="store_true", help="run on the fake sheet")
    ap.add_argument("--skip-sampling", action="store_true",
                    help="leave the frame and the draw alone")
    args = ap.parse_args()

    paths = TEST if args.test else REAL

    if args.test:
        run("make_test_data.py")
    elif not args.skip_sampling:
        # The export is untrusted input, so it is read in isolated mode.
        run("coursetable.py", isolated=True)
        run("sample_courses.py")

    for key in ("entries", "frame"):
        if not Path(paths[key]).exists():
            sys.exit(f"{paths[key]} not found")

    run("clean.py",
        "--entries", paths["entries"],
        "--frame", paths["frame"],
        "--displayed", paths["displayed"])
    run("model.py")
    run("bootstrap.py")
    run("gems.py")
    run("compare.py")
    run("tables.py")
    run("figures.py")
    run("summary.py")

    print("\n" + "=" * 70)
    print("done" + (" (TEST DATA -- nothing here may go in the report)" if args.test else ""))
    print("tables in output/, figures in report/figures/")


if __name__ == "__main__":
    main()
