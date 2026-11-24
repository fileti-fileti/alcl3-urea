#!/usr/bin/env python3
"""
build_seeds.py
--------------
Build the 15 multi-hypothesis starting boxes (3 compositions x 5 seeds) for
AlCl3:urea AIMD, by packing the extracted species (extract_species.py output)
with Packmol in cubic periodic boxes at the experimental density.

Two steps:
  1) setup : writes one folder per seed with packmol.inp + the species PDBs,
             and a run_packmol.sh that runs them all.
  2) check : reads each packed.pdb, writes packed.xyz (extended XYZ with the
             cell, ready for CP2K/ASE) and verifies, with the same bonding
             criterion as extract_species.py, that the box contains exactly the
             intended species (no accidental Al-Cl/Al-O contacts from packing).

Usage:
    python build_seeds.py setup --species species/pdb -o seeds
    bash seeds/run_packmol.sh            # needs Packmol >= 20.15 (pbc keyword)
    python build_seeds.py check -o seeds

How ions are placed:
    Packmol knows nothing about charges, and randomly placed cations and anions
    cluster by charge. Each ion therefore gets its first Al anchored (radius
    --anchor-r) to a site of a simple-cubic grid with checkerboard parity:
    cations on even sites, anions on odd sites (a coarse rock-salt pattern, like
    the NaCl-type placement of Carrasco-Busturia et al.). Orientations are free.
    Neutral species are packed freely around them.

Accidental bonds:
    The analysis criterion counts Al-Cl < 2.7 A and Al-O < 2.0 A as bonds.
    Al atoms are given a Packmol radius of --al-radius (default 1.8 A) while
    every other atom uses tolerance/2 = 1.0 A, so any intermolecular Al-X
    distance is >= 2.8 A after packing.

Requires: ase, numpy, scipy, Packmol >= 20.15; extract_species.py in the same folder.
"""
import argparse
import collections
import math
import os
import random
import sys

import numpy as np
from ase import Atoms
from ase.data import atomic_masses, atomic_numbers
from ase.io import write

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_species import components, find_bonds, label  # noqa: E402

NA = 6.02214076e23

# ---------------------------------------------------------------------------
# Compositions and seeds. Keys must match the PDB names written by
# extract_species.py (AlCl3 monomer is generated here if missing).
# rho at 333 K: 1.5 -> 1.5921 and 1.0 -> 1.5398 (Liu et al. 2017 / DTU);
# 1.3 is a linear interpolation: REPLACE with Liu et al. J. Mol. Liq. 247, 57 (2017).
# ---------------------------------------------------------------------------
COMPOSITIONS = {
    "r1.0": {"nAl": 36, "nU": 36, "rho": 1.5398, "seeds": {
        "reagentes": {"Al2Cl6": 18, "urea": 36},
        "neutro":    {"AlCl3U": 36},
        "ionico":    {"AlCl2U2_p": 18, "AlCl4_m": 18},
        "misto":     {"AlCl3U": 18, "AlCl2U2_p": 9, "AlCl4_m": 9},
        "fora_eq":   {"AlCl2U2_p": 12, "Al2Cl7_m": 12, "urea": 12},
    }},
    "r1.3": {"nAl": 39, "nU": 30, "rho": 1.571, "seeds": {
        "reagentes": {"Al2Cl6": 19, "AlCl3": 1, "urea": 30},
        "neutro":    {"AlCl3U": 21, "Al2Cl6U": 9},
        "ionicoA":   {"AlCl2U2_p": 15, "Al2Cl7_m": 9, "AlCl4_m": 6},
        "ionicoB":   {"Al2Cl5U2_p_iso2-0": 9, "AlCl2U2_p": 6, "AlCl4_m": 15},
        "misto":     {"AlCl3U": 10, "AlCl2U2_p": 10, "Al2Cl7_m": 9, "AlCl4_m": 1},
    }},
    "r1.5": {"nAl": 48, "nU": 32, "rho": 1.5921, "seeds": {
        "reagentes": {"Al2Cl6": 24, "urea": 32},
        "neutro":    {"AlCl3U": 16, "Al2Cl6U": 16},
        "ionicoA":   {"AlCl2U2_p": 16, "Al2Cl7_m": 16},
        "ionicoB":   {"Al2Cl5U2_p_iso2-0": 16, "AlCl4_m": 16},
        "misto":     {"AlCl3U": 8, "Al2Cl6U": 8, "AlCl2U2_p": 8, "Al2Cl7_m": 8},
    }},
}
PROVISIONAL_RHO = {"r1.3"}


# ----------------------------- PDB helpers ---------------------------------
def read_pdb(path):
    """Minimal PDB reader: element from cols 77-78 (fallback: atom name)."""
    syms, pos = [], []
    with open(path) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                el = line[76:78].strip() or "".join(c for c in line[12:16] if c.isalpha())[:2]
                syms.append(el.capitalize())
                pos.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return syms, np.array(pos)


def write_simple_pdb(path, syms, pos, resname):
    count = collections.Counter()
    with open(path, "w") as f:
        for k, (s, p) in enumerate(zip(syms, pos), 1):
            count[s] += 1
            f.write(f"HETATM{k:5d} {(s.upper() + str(count[s]))[:4]:<4s} {resname:>3s} A{1:4d}    "
                    f"{p[0]:8.3f}{p[1]:8.3f}{p[2]:8.3f}{1.0:6.2f}{0.0:6.2f}          {s.upper():>2s}\n")
        f.write("END\n")


def make_alcl3(path):
    d = 2.07  # Al-Cl, trigonal planar monomer
    pos = [[0, 0, 0]] + [[d * math.cos(a), d * math.sin(a), 0.0]
                         for a in (0, 2 * math.pi / 3, 4 * math.pi / 3)]
    write_simple_pdb(path, ["Al", "Cl", "Cl", "Cl"], np.array(pos), "AL3")


def species_info(path):
    syms, _ = read_pdb(path)
    c = collections.Counter(syms)
    return {
        "nAl": c.get("Al", 0), "nCl": c.get("Cl", 0), "nU": c.get("C", 0),
        "charge": 3 * c.get("Al", 0) - c.get("Cl", 0),
        "mass": sum(atomic_masses[atomic_numbers[s]] for s in syms),
        "natoms": len(syms),
        "al_idx": [k + 1 for k, s in enumerate(syms) if s == "Al"],  # 1-based for Packmol
    }


# ------------------------------- setup -------------------------------------
def grid_sites(L, n_cat, n_an, rng):
    n = 2
    while (n ** 3 + 1) // 2 < n_cat or n ** 3 // 2 < n_an:
        n += 1
    h = L / n
    even, odd = [], []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                site = ((i + 0.5) * h, (j + 0.5) * h, (k + 0.5) * h)
                (even if (i + j + k) % 2 == 0 else odd).append(site)
    rng.shuffle(even)
    rng.shuffle(odd)
    return even[:n_cat], odd[:n_an], n


def setup(args):
    spdir = os.path.abspath(args.species)
    if not os.path.exists(os.path.join(spdir, "AlCl3.pdb")):
        make_alcl3(os.path.join(spdir, "AlCl3.pdb"))
        print(f"note: AlCl3.pdb (trigonal planar monomer) generated in {spdir}")
    needed = {sp for comp in COMPOSITIONS.values() for seed in comp["seeds"].values() for sp in seed}
    missing = [sp for sp in sorted(needed) if not os.path.exists(os.path.join(spdir, sp + ".pdb"))]
    if missing:
        sys.exit(f"missing species PDBs in {spdir}: {missing}")
    info = {sp: species_info(os.path.join(spdir, sp + ".pdb")) for sp in needed}

    rng = random.Random(args.seed)
    os.makedirs(args.outdir, exist_ok=True)
    runlines = ["#!/bin/bash", "# runs Packmol in every seed folder", f'PACKMOL="${{PACKMOL:-{args.packmol}}}"',
                'cd "$(dirname "$0")"']
    summary = []
    for rname, comp in COMPOSITIONS.items():
        rho = comp["rho"]
        for sname, seed in comp["seeds"].items():
            # stoichiometry and neutrality checks
            nAl = sum(n * info[sp]["nAl"] for sp, n in seed.items())
            nU = sum(n * info[sp]["nU"] for sp, n in seed.items())
            nCl = sum(n * info[sp]["nCl"] for sp, n in seed.items())
            q = sum(n * info[sp]["charge"] for sp, n in seed.items())
            if (nAl, nU, nCl, q) != (comp["nAl"], comp["nU"], 3 * comp["nAl"], 0):
                sys.exit(f"{rname}/{sname}: Al={nAl} U={nU} Cl={nCl} q={q} "
                         f"(expected Al={comp['nAl']} U={comp['nU']} Cl={3 * comp['nAl']} q=0)")
            mass = sum(n * info[sp]["mass"] for sp, n in seed.items())
            natoms = sum(n * info[sp]["natoms"] for sp, n in seed.items())
            L = (mass / NA / rho * 1e24) ** (1 / 3)

            folder = os.path.join(args.outdir, rname, sname)
            os.makedirs(folder, exist_ok=True)
            for sp in seed:
                src = os.path.join(spdir, sp + ".pdb")
                with open(src) as fi, open(os.path.join(folder, sp + ".pdb"), "w") as fo:
                    fo.write(fi.read())

            cations = [sp for sp in seed if info[sp]["charge"] > 0 for _ in range(seed[sp])]
            anions = [sp for sp in seed if info[sp]["charge"] < 0 for _ in range(seed[sp])]
            rng.shuffle(cations)
            rng.shuffle(anions)
            csites, asites, ngrid = grid_sites(L, len(cations), len(anions), rng) if (cations or anions) else ([], [], 0)

            inp = [f"# {rname} / {sname}: {natoms} atoms, rho = {rho} g/cm3, L = {L:.4f} A",
                   f"tolerance {args.tol}", "filetype pdb", "output packed.pdb",
                   f"seed {rng.randint(1, 10**7)}", f"pbc 0. 0. 0. {L:.4f} {L:.4f} {L:.4f}", ""]

            def al_radius_block(sp, skip=()):
                lines = []
                rest = [a for a in info[sp]["al_idx"] if a not in skip]
                if rest:
                    lines += [f"  atoms {' '.join(map(str, rest))}", f"    radius {args.al_radius}", "  end atoms"]
                return lines

            for sp_list, sites in ((cations, csites), (anions, asites)):
                for sp, (x, y, z) in zip(sp_list, sites):
                    anchor = info[sp]["al_idx"][0]
                    inp += [f"structure {sp}.pdb", "  number 1",
                            f"  atoms {anchor}", f"    radius {args.al_radius}",
                            f"    inside sphere {x:.3f} {y:.3f} {z:.3f} {args.anchor_r}", "  end atoms"]
                    inp += al_radius_block(sp, skip=(anchor,))
                    inp += ["end structure", ""]
            for sp, n in seed.items():
                if info[sp]["charge"] != 0:
                    continue
                inp += [f"structure {sp}.pdb", f"  number {n}"]
                inp += al_radius_block(sp)
                inp += ["end structure", ""]
            with open(os.path.join(folder, "packmol.inp"), "w") as f:
                f.write("\n".join(inp) + "\n")
            with open(os.path.join(folder, "target.txt"), "w") as f:
                f.write(f"L {L:.6f}\nrho {rho}\nnatoms {natoms}\n")
                for sp, n in seed.items():
                    f.write(f"{sp} {n}\n")

            rel = os.path.join(rname, sname)
            runlines.append(f'echo "== {rel}"; ( cd {rel} && "$PACKMOL" < packmol.inp > packmol.log 2>&1 '
                            f'&& grep -q "Success" packmol.log && echo "   ok" || echo "   CHECK {rel}/packmol.log" )')
            flag = "  [rho provisional]" if rname in PROVISIONAL_RHO else ""
            grid = f"  ions on {ngrid}^3 grid" if ngrid else ""
            summary.append(f"{rel:18s} {natoms:4d} atoms  L = {L:7.3f} A{grid}{flag}")

    run = os.path.join(args.outdir, "run_packmol.sh")
    with open(run, "w") as f:
        f.write("\n".join(runlines) + "\n")
    os.chmod(run, 0o755)
    print("\n".join(summary))
    print(f"\nnext: bash {run}   then   python {os.path.basename(__file__)} check -o {args.outdir}")


# ------------------------------- check -------------------------------------
def check(args):
    bad = 0
    for rname, comp in COMPOSITIONS.items():
        for sname in comp["seeds"]:
            folder = os.path.join(args.outdir, rname, sname)
            packed = os.path.join(folder, "packed.pdb")
            if not os.path.exists(packed):
                print(f"{rname}/{sname:10s} MISSING packed.pdb")
                bad += 1
                continue
            target = {}
            with open(os.path.join(folder, "target.txt")) as f:
                for line in f:
                    k, v = line.split()
                    target[k] = float(v) if k in ("L", "rho") else int(v)
            L = target.pop("L")
            target.pop("rho")
            natoms = target.pop("natoms")
            syms, pos = read_pdb(packed)
            atoms = Atoms(syms, positions=pos, cell=[L, L, L], pbc=True)
            atoms.wrap()
            i, j, _ = find_bonds(atoms)
            adj = collections.defaultdict(list)
            for a, b in zip(i, j):
                adj[a].append((b, None))
            ncomp, lab = components(len(atoms), i, j)
            census = collections.Counter()
            for c in range(ncomp):
                idx = list(np.where(lab == c)[0])
                name, _ = label([syms[a] for a in idx], idx, adj, syms)
                census[name] += 1
            # nearest intermolecular heavy-atom distance
            d = atoms.get_all_distances(mic=True)
            same = lab[:, None] == lab[None, :]
            heavy = np.array([s != "H" for s in syms])
            mask = ~same & heavy[:, None] & heavy[None, :]
            dmin = d[mask].min() if mask.any() else float("nan")
            ok = census == collections.Counter(target) and len(atoms) == natoms
            bad += not ok
            write(os.path.join(folder, "packed.xyz"), atoms, format="extxyz")
            status = "OK " if ok else "MISMATCH"
            print(f"{rname}/{sname:10s} {status} {len(atoms):4d} atoms  min inter heavy-heavy {dmin:4.2f} A")
            if not ok:
                print(f"    target: {dict(target)}\n    found : {dict(census)}")
    print("\nall seeds OK" if bad == 0 else f"\n{bad} seed(s) need attention")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup")
    s.add_argument("--species", default="species/pdb", help="folder with the species PDBs")
    s.add_argument("-o", "--outdir", default="seeds")
    s.add_argument("--tol", type=float, default=2.0, help="Packmol tolerance (A)")
    s.add_argument("--al-radius", type=float, default=1.8, help="Packmol radius for Al atoms (A)")
    s.add_argument("--anchor-r", type=float, default=2.0, help="radius of the ion anchor sphere (A)")
    s.add_argument("--seed", type=int, default=2026, help="random seed for site assignment")
    s.add_argument("--packmol", default="packmol", help="Packmol executable")
    c = sub.add_parser("check")
    c.add_argument("-o", "--outdir", default="seeds")
    args = ap.parse_args()
    setup(args) if args.cmd == "setup" else check(args)


if __name__ == "__main__":
    main()
