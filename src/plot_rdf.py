#!/usr/bin/env python3
"""Grid plots of the partial RDFs written by src/rdf.py.

One figure per (temperature, molar ratio r): a 2 x 5 grid, one panel per atom pair, one
line per seed (colour and line style fixed per seed across all figures), shaded +-1 block
SE. Pairs with a dominant bonded first peak get an inset that zooms beyond the first shell.

Usage (numpy + matplotlib: call an env's python explicitly, e.g. the `analysis` env):
  plot_rdf.py <results_dir> -o <outdir> [--source aimd]
Writes rdf.<source>.T<T>.r<rr>.png/.pdf per group and rdf.<source>.all.pdf (all pages).
"""
import argparse
import glob
import os
import subprocess
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# seed -> (colour, line style, legend label); colours: validated categorical order
SEEDS = {
    "ion":  ("#2a78d6", "-",  r"ion: ionic, [AlCl$_2$U$_2$]$^+$ + AlCl$_4^-$"),
    "ionA": ("#2a78d6", "-",  r"ionA: ionic A, [AlCl$_2$U$_2$]$^+$ cation"),
    "ionB": ("#eb6834", "--", r"ionB: ionic B, [Al$_2$Cl$_5$U$_2$]$^+$ cation"),
    "mist": ("#1baf7a", "-.", "mist: mixed adducts + ion pairs"),
    "neut": ("#eda100", ":",  "neut: neutral adducts only"),
    "reag": ("#e87ba4", (0, (6, 1.5, 1, 1.5, 1, 1.5)), r"reag: reagents, Al$_2$Cl$_6$ + free urea"),
    "fora": ("#008300", (0, (8, 2.5)), "fora: off-equilibrium start"),
}
SEED_ORDER = ["ion", "ionA", "ionB", "mist", "neut", "reag", "fora"]
# (pair, role, inset start in A or None); row 1: Al and anions, row 2: H-bonds and urea
PANELS = [
    ("Al-Cl", "Al shell: terminal vs bridging Cl", 2.6),
    ("Al-O", "urea O bound to Al", 2.3),
    ("Al-N", "N-binding check, 2nd shell", None),
    ("Al-Al", "Al dimers vs separate Al", None),
    ("Cl-Cl", r"AlCl$_4$ tetrahedra, anion packing", None),
    ("Cl-H", r"N$-$H$\cdots$Cl hydrogen bonds", None),
    ("O-H", r"N$-$H$\cdots$O H-bonds (+ intra)", None),
    ("C-O", "urea C=O bond", 1.8),
    ("C-N", "urea C$-$N bond", 1.8),
    ("N-H", "urea N$-$H bond", 1.4),
]
RMAX = 9.7


def load(path):
    cols = open(path).readline().strip().split(",")
    a = np.loadtxt(path, delimiter=",", skiprows=1)
    return {c: a[:, i] for i, c in enumerate(cols)}


def commit():
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        return subprocess.check_output(["git", "-C", here, "rev-parse", "--short", "HEAD"],
                                       universal_newlines=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def style_axis(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=INK2, labelsize=8, width=0.8)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.axhline(1.0, color=INK2, linewidth=0.7, linestyle=(0, (2, 2)), zorder=1)


def draw(ax, runs, pair, rlo=0.0):
    for seed, d in runs:
        color, ls, _ = SEEDS[seed]
        r, g, se = d["r_center_A"], d["g_" + pair], d["se_" + pair]
        m = r >= rlo
        ax.fill_between(r[m], (g - se)[m], (g + se)[m], color=color, alpha=0.18, linewidth=0)
        ax.plot(r[m], g[m], color=color, linestyle=ls, linewidth=1.4)


def figure(T, rr, runs, source, foot):
    fig, axes = plt.subplots(2, 5, figsize=(17, 8.3))
    fig.subplots_adjust(left=0.045, right=0.99, top=0.775, bottom=0.085, wspace=0.22, hspace=0.42)
    for ax, (pair, role, inset) in zip(axes.ravel(), PANELS):
        style_axis(ax)
        draw(ax, runs, pair)
        ax.set_xlim(0, RMAX)
        ax.set_ylim(bottom=0)
        a, b = pair.split("-")
        ax.set_title("{}$-${}".format(a, b), loc="left", fontsize=12, fontweight="bold",
                     color=INK, pad=14)
        ax.text(0.0, 1.015, role, transform=ax.transAxes, fontsize=8.5, color=INK2,
                ha="left", va="bottom")
        if inset is not None:
            ins = ax.inset_axes([0.40, 0.42, 0.57, 0.50])
            style_axis(ins)
            draw(ins, runs, pair, rlo=inset)
            ins.set_xlim(inset, RMAX)
            top = max(float(((d["g_" + pair] + d["se_" + pair])[d["r_center_A"] >= inset]).max())
                      for _, d in runs)
            ins.set_ylim(0, 1.08 * top)
            ins.tick_params(labelsize=7)
            ins.set_title("zoom: r > {:g} Å".format(inset), fontsize=7.5, color=INK2,
                          pad=2)
    for ax in axes[1]:
        ax.set_xlabel("r (Å)", fontsize=10, color=INK)
    for ax in axes[:, 0]:
        ax.set_ylabel("g(r)", fontsize=10, color=INK)
    r_val = {"r10": "1.0", "r13": "1.3", "r15": "1.5"}[rr]
    fig.text(0.045, 0.970, r"AlCl$_3$:urea, molar ratio r = {}, T = {} K: {} partial RDFs".format(
        r_val, T, source.upper()), fontsize=15, fontweight="bold", color=INK, ha="left")
    if T == 333:
        note = ("Local structure of each starting speciation (seed); each run keeps its seed's "
                "speciation over 6 ps, so seeds are not averaged.")
    else:
        note = ("Box at the 333 K density (elevated pressure): reference for MLMD tests, "
                "not for structural characterisation.")
    fig.text(0.045, 0.940, "PBE-D3(BJ)/DZVP-MOLOPT-SR, 5 ps production (1001 frames); all pairs, "
             "intra + intermolecular; shaded band: ±1 block standard error (5 blocks); "
             "grey dashed line: g = 1.", fontsize=9.5, color=INK2, ha="left")
    fig.text(0.045, 0.918, note, fontsize=9.5, color=INK2, ha="left")
    handles = [plt.Line2D([], [], color=SEEDS[s][0], linestyle=SEEDS[s][1], linewidth=2)
               for s, _ in runs]
    fig.legend(handles, [SEEDS[s][2] for s, _ in runs], loc="upper left",
               bbox_to_anchor=(0.04, 0.905), ncol=min(len(runs), 5), frameon=False,
               fontsize=9.5, handlelength=3.2, columnspacing=1.8, title="Seed (starting speciation)",
               title_fontsize=9.5, alignment="left", labelcolor=INK)
    fig.text(0.99, 0.012, foot, fontsize=7.5, color=INK2, ha="right")
    return fig


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("results_dir")
    p.add_argument("-o", "--outdir", required=True)
    p.add_argument("--source", default="aimd")
    a = p.parse_args()
    groups = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(a.results_dir, "*.{}.rdf.csv".format(a.source)))):
        system, temp = os.path.basename(f).split(".")[:2]
        rr, seed = system.split("_", 1)
        groups[(int(temp[1:]), rr)].append((seed, load(f)))
    os.makedirs(a.outdir, exist_ok=True)
    foot = "src/plot_rdf.py @ {} · data: {}".format(commit(), os.path.basename(
        os.path.normpath(a.results_dir)))
    allpdf = os.path.join(a.outdir, "rdf.{}.all.pdf".format(a.source))
    with PdfPages(allpdf) as pdf:
        for (T, rr), runs in sorted(groups.items()):
            runs.sort(key=lambda x: SEED_ORDER.index(x[0]))
            fig = figure(T, rr, runs, a.source, foot)
            stem = os.path.join(a.outdir, "rdf.{}.T{}.{}".format(a.source, T, rr))
            fig.savefig(stem + ".png", dpi=200, facecolor="white")
            fig.savefig(stem + ".pdf", facecolor="white")
            pdf.savefig(fig, facecolor="white")
            plt.close(fig)
            print("wrote {}.png/.pdf ({} seeds: {})".format(stem, len(runs),
                                                           ", ".join(s for s, _ in runs)))
    print("wrote", allpdf)


if __name__ == "__main__":
    main()
