"""Build every figure in the report, as PDF for LaTeX and PNG for the slides."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

from model import DISCIPLINES, load_clean

OUT = Path("report/figures")

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e2e1dc"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]

LABEL = {"humanities": "Humanities", "social_sciences": "Social Sciences", "stem": "STEM"}
SIZE_ORDER = ["seminar", "mid", "lecture"]
SIZE_LABEL = {"seminar": "Seminar\n(<20)", "mid": "Mid\n(20-79)", "lecture": "Lecture\n(80+)"}


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": GRID,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "font.size": 9,
        "axes.titlesize": 10,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "lines.linewidth": 1.8,
    })


def tidy(ax, yzero=False):
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    if yzero:
        ax.axhline(0, color=INK_SOFT, linewidth=0.9, zorder=2)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"  {name}.pdf / {name}.png")


def fig1_weights(ci):
    """Standardized weights per discipline, OCE against CourseTable."""
    panels = [
        ("Workload", "workload", "ct_workload"),
        ("Teaching quality", "teaching", "ct_professor"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2), sharey=True)
    x = np.arange(len(DISCIPLINES))
    width = 0.34

    for ax, (title, oce_param, ct_param) in zip(axes, panels):
        for k, (label, param, colour) in enumerate(
                [("OCE", oce_param, SERIES[0]), ("CourseTable", ct_param, SERIES[1])]):
            est, lo, hi = [], [], []
            for d in DISCIPLINES:
                row = ci[(ci["discipline"] == d) & (ci["param"] == param)]
                if row.empty:
                    est.append(np.nan); lo.append(0); hi.append(0)
                    continue
                e = float(row["estimate"].iloc[0])
                est.append(e)
                lo.append(max(0.0, e - float(row["ci_lo"].iloc[0])))
                hi.append(max(0.0, float(row["ci_hi"].iloc[0]) - e))
            ax.bar(x + (k - 0.5) * (width + 0.02), est, width,
                   label=label, color=colour, zorder=3)
            ax.errorbar(x + (k - 0.5) * (width + 0.02), est, yerr=[lo, hi],
                        fmt="none", ecolor=INK_SOFT, elinewidth=1.1, capsize=3, zorder=4)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels([LABEL[d] for d in DISCIPLINES], fontsize=8)
        tidy(ax, yzero=True)

    axes[0].set_ylabel("Standardized weight")
    axes[0].legend(loc="lower left", fontsize=8)
    fig.suptitle("Weight on overall rating, with 95% bootstrap intervals", y=1.02, fontsize=10)
    save(fig, "fig1_weights")


def fig2_actual_vs_predicted(resid, gems):
    """Where the model lands, and which courses sit far above it."""
    oce = resid[resid["model"] == "oce"]
    flagged = set(gems[gems["model"] == "oce"]["course_code"])

    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    lims = [min(oce["predicted_std"].min(), oce["actual_std"].min()) - 0.4,
            max(oce["predicted_std"].max(), oce["actual_std"].max()) + 0.4]
    ax.plot(lims, lims, color=INK_SOFT, linewidth=1.0, linestyle=(0, (4, 3)), zorder=2)

    for colour, d in zip(SERIES, DISCIPLINES):
        sub = oce[oce["discipline"] == d]
        ax.scatter(sub["predicted_std"], sub["actual_std"], s=46, color=colour,
                   edgecolor=SURFACE, linewidth=1.0, label=LABEL[d], zorder=3)

    for _, row in oce[oce["course_code"].isin(flagged)].iterrows():
        ax.annotate(row["course_code"], (row["predicted_std"], row["actual_std"]),
                    textcoords="offset points", xytext=(7, -2), fontsize=7, color=INK)

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Predicted overall rating (standardized)")
    ax.set_ylabel("Actual overall rating (standardized)")
    ax.set_title("Labelled courses are the flagged hidden gems")
    ax.legend(fontsize=8, loc="upper left")
    tidy(ax)
    save(fig, "fig2_actual_vs_predicted")


def fig3_gem_rate(resid, gems):
    """Gem rate by class size, split by discipline."""
    oce = resid[resid["model"] == "oce"].copy()
    flagged = set(gems[gems["model"] == "oce"]["course_code"])
    oce["is_gem"] = oce["course_code"].isin(flagged)

    bins = [b for b in SIZE_ORDER if b in set(oce["size_bin"])]
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    x = np.arange(len(bins))
    width = 0.26

    for k, (colour, d) in enumerate(zip(SERIES, DISCIPLINES)):
        rates, counts = [], []
        for b in bins:
            cell = oce[(oce["discipline"] == d) & (oce["size_bin"] == b)]
            rates.append(100 * cell["is_gem"].mean() if len(cell) else 0.0)
            counts.append(len(cell))
        pos = x + (k - 1) * (width + 0.02)
        ax.bar(pos, rates, width, color=colour, label=LABEL[d], zorder=3)
        for xi, n in zip(pos, counts):
            ax.annotate(f"n={n}", (xi, 0), textcoords="offset points", xytext=(0, 3),
                        ha="center", fontsize=6.5, color=INK_SOFT)

    ax.set_xticks(x)
    ax.set_xticklabels([SIZE_LABEL[b] for b in bins], fontsize=8)
    ax.set_ylabel("Gems (% of courses in cell)")
    ax.set_title("Hidden-gem rate by class size")
    ax.legend(fontsize=8)
    tidy(ax)
    save(fig, "fig3_gem_rate")


def fig4_circularity(df):
    """Does CourseTable's professor score track the overall question or the teaching ones?"""
    panels = [("overall", "OCE overall assessment"), ("teaching", "OCE teaching quality (Q5/Q6)")]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.6), sharey=True)

    for ax, (col, xlabel) in zip(axes, panels):
        sub = df.dropna(subset=[col, "ct_professor"])
        for colour, d in zip(SERIES, DISCIPLINES):
            part = sub[sub["discipline"] == d]
            ax.scatter(part[col], part["ct_professor"], s=38, color=colour,
                       edgecolor=SURFACE, linewidth=0.9, label=LABEL[d], zorder=3)
        if len(sub) > 2:
            slope, intercept = np.polyfit(sub[col], sub["ct_professor"], 1)
            xs = np.linspace(sub[col].min(), sub[col].max(), 50)
            ax.plot(xs, slope * xs + intercept, color=INK_SOFT, linewidth=1.2,
                    linestyle=(0, (4, 3)), zorder=2)
            r = sub[col].corr(sub["ct_professor"])
            ax.set_title(f"r = {r:.2f}", fontsize=9)
        else:
            ax.set_title(xlabel, fontsize=9)
        ax.set_xlabel(xlabel)
        tidy(ax)

    axes[0].set_ylabel("CourseTable professor rating")
    axes[0].legend(fontsize=8, loc="lower right")
    fig.suptitle("CourseTable's professor score against two different OCE questions",
                 y=1.04, fontsize=10)
    save(fig, "fig4_circularity")


def fig5_projection():
    """The geometry: y projected onto Col(A), residual perpendicular to it."""
    fig, ax = plt.subplots(figsize=(5.2, 3.8))

    corners = np.array([[0.0, 0.0], [4.0, 0.6], [5.2, 1.6], [1.2, 1.0]])
    ax.add_patch(Polygon(corners, closed=True, facecolor=SERIES[0], alpha=0.10,
                         edgecolor=SERIES[0], linewidth=1.2, zorder=1))

    O = np.array([0.9, 0.45])
    P = np.array([3.2, 1.0])
    Y = P + np.array([0.0, 1.9])

    def arrow(a, b, colour, lw=1.9):
        ax.annotate("", xy=b, xytext=a,
                    arrowprops=dict(arrowstyle="-|>", color=colour, linewidth=lw,
                                    shrinkA=0, shrinkB=0, mutation_scale=14), zorder=4)

    arrow(O, Y, SERIES[1])
    arrow(O, P, SERIES[0])
    arrow(P, Y, SERIES[2])

    u = (O - P) / np.linalg.norm(O - P)
    v = np.array([0.0, 1.0])
    m = 0.2
    ax.add_patch(Polygon([P, P + m * u, P + m * u + m * v, P + m * v], closed=True,
                         facecolor="none", edgecolor=INK_SOFT, linewidth=1.0, zorder=5))

    ax.text(*(Y + np.array([0.08, 0.1])), r"$\mathbf{y}$", fontsize=12, color=SERIES[1])
    ax.text(2.5, 0.42, r"$\hat{\mathbf{y}} = A\hat{\beta} = P\mathbf{y}$",
            fontsize=10, color=SERIES[0], ha="center")
    ax.text(*((P + Y) / 2 + np.array([0.14, 0.0])),
            r"$\mathbf{e} = \mathbf{y} - \hat{\mathbf{y}}$", fontsize=10, color=SERIES[2])
    ax.text(4.95, 1.74, r"$\mathrm{Col}(A)$", fontsize=10, color=SERIES[0])
    ax.text(*(O + np.array([-0.3, -0.05])), r"$\mathbf{0}$", fontsize=10, color=INK_SOFT)
    ax.text(1.1, 3.05, r"$A^{\mathsf{T}}\mathbf{e} = \mathbf{0}$", fontsize=10, color=INK)

    ax.set_xlim(-0.5, 5.9)
    ax.set_ylim(-0.4, 3.4)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "fig5_projection")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clean", default="data/processed/clean.csv")
    args = ap.parse_args()

    style()
    df = load_clean(args.clean)
    ci = pd.read_csv("output/beta_ci.csv")
    resid = pd.read_csv("output/residuals.csv")
    gems = pd.read_csv("output/gems.csv")

    print("figures:")
    fig1_weights(ci)
    fig2_actual_vs_predicted(resid, gems)
    fig3_gem_rate(resid, gems)
    fig4_circularity(df)
    fig5_projection()
    print(f"\nwrote 5 figures to {OUT}/ as PDF and PNG")


if __name__ == "__main__":
    main()
