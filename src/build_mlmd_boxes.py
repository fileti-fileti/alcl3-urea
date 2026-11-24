#!/usr/bin/env python3
"""
build_mlmd_boxes.py -- large (~1500 atoms) AlCl3:urea boxes for MLMD, with EXACT Al:urea ratios.

Reuses build_seeds.py (same folder): same species PDBs, same Packmol recipe (ions anchored on a checkerboard
grid, Al radius 1.8 A), same 5 seed families per composition as the AIMD boxes, only scaled up.

  python build_mlmd_boxes.py plan [--ratios r1.0 r1.5 ...]          # sizes/counts only, no files (default: all 7)
  python build_mlmd_boxes.py setup  --species species/pdb -o mlmd_boxes [--natoms 1500] [--k r1.0=126 ...]
  bash mlmd_boxes/run_packmol.sh                                    # Packmol >= 20.15
  python build_mlmd_boxes.py check  -o mlmd_boxes                   # species census per box (same test as AIMD seeds)
  python build_mlmd_boxes.py export -o mlmd_boxes                   # start.data (LAMMPS), manifest.csv, README_boxes.md

Notes: r=1.0/1.3/1.5 are in the AIMD training set; 1.2/1.4 interpolate; 1.6/1.7 EXTRAPOLATE in composition (all-ionic
seeds cannot exceed Al:urea = 1.5, so for r>1.5 the ionic seeds carry Al2Cl6 as the excess Lewis acid). Densities for
r != 1.0, 1.5 are linear in r and provisional (NPT fixes them).

Result (self-contained, ready to rsync to SDumont):
  mlmd_boxes/<r>/<seed>/{packed.xyz, start.data, packmol.inp, target.txt, packmol.log}
  mlmd_boxes/manifest.csv, mlmd_boxes/README_boxes.md

Exact ratios: nAl:nU = a:b (1:1, 13:10, 3:2) times an integer k. The script picks k so that natoms is closest to
--natoms AND every seed family has an exact integer solution (Al, urea, Cl = 3 Al, total charge 0). No box is
ever rounded: a failure to find an exact solution aborts.
LAMMPS atom types (fixed, same order in every box):  1 Al  2 C  3 Cl  4 H  5 N  6 O
"""
import argparse, collections, csv, itertools, math, os, sys
from fractions import Fraction

import numpy as np
from ase.data import atomic_masses, atomic_numbers
from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_seeds as bs  # noqa: E402

RATIOS = {"r1.0": (1, 1), "r1.2": (6, 5), "r1.3": (13, 10), "r1.4": (7, 5),
          "r1.5": (3, 2), "r1.6": (8, 5), "r1.7": (17, 10)}               # nAl : nU (exact fractions)
# AIMD seed family used as the proportion template for each ratio (nearest trained composition)
TEMPLATE = {"r1.0": "r1.0", "r1.2": "r1.3", "r1.3": "r1.3", "r1.4": "r1.5",
            "r1.5": "r1.5", "r1.6": "r1.5", "r1.7": "r1.5"}
TRAINED = {"r1.0", "r1.3", "r1.5"}          # compositions present in the AIMD training set
MEASURED_RHO = {"r1.0", "r1.5"}             # others: linear interpolation/extrapolation, REPLACE with Liu et al. 2017
TYPES = ["Al", "C", "Cl", "H", "N", "O"]

# (nAl, nCl, nUrea) of each species; charge = 3 nAl - nCl; natoms = nAl + nCl + 8 nUrea.
# Only used to solve the integer counts; build_seeds.setup re-verifies everything from the PDBs.
FORMULA = {"AlCl3": (1, 3, 0), "Al2Cl6": (2, 6, 0), "urea": (0, 0, 1), "AlCl3U": (1, 3, 1),
           "AlCl2U2_p": (1, 2, 2), "AlCl4_m": (1, 4, 0), "Al2Cl7_m": (2, 7, 0), "Al2Cl6U": (2, 6, 1),
           "Al2Cl5U2_p_iso2-0": (2, 5, 2)}
ORIG = {r: (c["nAl"], c["seeds"]) for r, c in bs.COMPOSITIONS.items()}     # AIMD templates (proportions)
_R = {r: c["rho"] for r, c in bs.COMPOSITIONS.items()}
def rho_of(r):
    if r in _R and r in MEASURED_RHO:
        return _R[r]
    x = float(r[1:])                                   # linear in r between r=1.0 and r=1.5 (extrapolated outside)
    return _R["r1.0"] + (x - 1.0) * (_R["r1.5"] - _R["r1.0"]) / 0.5
RHO = {r: rho_of(r) for r in RATIOS}


def sp_info(sp):
    a, c, u = FORMULA[sp]
    return a, u, 3 * a - c, a + c + 8 * u          # nAl, nUrea, charge, natoms


def solve_seed(nAl, nU, orig_counts, orig_nAl):
    """Exact integer counts (Al, urea and q=0 balances hold exactly) closest to the AIMD seed family scaled to
    nAl. Species absent from the AIMD seed (AlCl3, urea, Al2Cl6) may be added as fillers, at a penalty.
    Solved as a small MILP (scipy >= 1.9); returns (cost, {species: n}) or None if infeasible."""
    from scipy.optimize import Bounds, LinearConstraint, milp
    sp = list(orig_counts) + [e for e in ("AlCl3", "urea", "Al2Cl6") if e not in orig_counts]
    k = len(sp)
    s = nAl / orig_nAl
    t = np.array([orig_counts.get(x, 0) * s for x in sp], float)
    w = np.array([1.0 / max(ti, 1.0) if x in orig_counts else 0.5 for x, ti in zip(sp, t)])   # relative L1; fillers cost
    # variables: n_1..n_k (integer >=0), d_1..d_k (>= |n - t|)
    c = np.concatenate([np.zeros(k), w])
    A_eq = np.array([[sp_info(x)[0] for x in sp] + [0] * k,
                     [sp_info(x)[1] for x in sp] + [0] * k,
                     [sp_info(x)[2] for x in sp] + [0] * k], float)
    b_eq = np.array([nAl, nU, 0], float)
    I = np.eye(k)
    A_ub = np.block([[I, -I], [-I, -I]])
    b_ub = np.concatenate([t, -t])
    cons = [LinearConstraint(A_eq, b_eq, b_eq), LinearConstraint(A_ub, -np.inf, b_ub)]
    res = milp(c, constraints=cons, integrality=np.concatenate([np.ones(k), np.zeros(k)]),
               bounds=Bounds(np.zeros(2 * k), np.full(2 * k, np.inf)))
    if not res.success:
        return None
    n = np.rint(res.x[:k]).astype(int)
    counts = {x: int(v) for x, v in zip(sp, n) if v}
    assert sum(v * sp_info(x)[0] for x, v in counts.items()) == nAl      # exactness guard
    assert sum(v * sp_info(x)[1] for x, v in counts.items()) == nU
    assert sum(v * sp_info(x)[2] for x, v in counts.items()) == 0
    return (float(res.fun), counts)


def choose_k(r, natoms_target):
    a, b = RATIOS[r]
    cands = []
    for k in range(1, 400):
        nAl, nU = a * k, b * k
        N = nAl * 4 + nU * 8
        if abs(N - natoms_target) > 0.05 * natoms_target:
            continue
        sols = {s: solve_seed(nAl, nU, cnt, ORIG[TEMPLATE[r]][0]) for s, cnt in ORIG[TEMPLATE[r]][1].items()}
        if any(v is None for v in sols.values()):
            continue
        # "filler" = species that were NOT in the AIMD seed and had to be added to close the integer balance
        filler = sum(n for s, v in sols.items() for sp, n in v[1].items() if sp not in ORIG[TEMPLATE[r]][1][s])
        cands.append((filler, abs(N - natoms_target), k))
    if not cands:
        sys.exit(f"{r}: no exact solution near {natoms_target} atoms")
    return min(cands)[2]  # fewest filler species first, then closest to the target size


def build_compositions(natoms, kover, ratios=None):
    comps = {}
    for r, (a, b) in RATIOS.items():
        if ratios and r not in ratios:
            continue
        k = kover.get(r) or choose_k(r, natoms)
        nAl, nU = a * k, b * k
        seeds = {}
        for s, cnt in ORIG[TEMPLATE[r]][1].items():
            res = solve_seed(nAl, nU, cnt, ORIG[TEMPLATE[r]][0])
            if res is None:
                sys.exit(f"{r}/{s}: no exact integer solution for nAl={nAl}, nU={nU}")
            seeds[s] = res[1]
        comps[r] = {"nAl": nAl, "nU": nU, "rho": RHO[r], "seeds": seeds}
    return comps


def plan_table(comps):
    print(f"{'box':16s} {'nAl':>4s} {'nU':>4s} {'natoms':>6s} {'L(A)':>7s}  species")
    for r, c in comps.items():
        for s, sp in c["seeds"].items():
            mass = sum(n * sum(atomic_masses[atomic_numbers[e]] * m for e, m in _atoms(k).items()) for k, n in sp.items())
            N = sum(n * sp_info(k)[3] for k, n in sp.items())
            L = (mass / bs.NA / c["rho"] * 1e24) ** (1 / 3)
            print(f"{r + '/' + s:16s} {c['nAl']:4d} {c['nU']:4d} {N:6d} {L:7.3f}  {sp}"
                  + ("  [rho provisional]" if r in bs.PROVISIONAL_RHO else ""))


def _atoms(sp):
    a, c, u = FORMULA[sp]
    return {"Al": a, "Cl": c, "C": u, "H": 4 * u, "N": 2 * u, "O": u}


def apply(comps):
    bs.COMPOSITIONS.clear()
    bs.COMPOSITIONS.update(comps)
    bs.PROVISIONAL_RHO.clear()
    bs.PROVISIONAL_RHO.update(r for r in comps if r not in MEASURED_RHO)


def cmd_plan(a):
    comps = build_compositions(a.natoms, parse_k(a.k), a.ratios)
    plan_table(comps)


def parse_k(lst):
    return {x.split("=")[0]: int(x.split("=")[1]) for x in (lst or [])}


def cmd_setup(a):
    comps = build_compositions(a.natoms, parse_k(a.k), a.ratios)
    plan_table(comps)
    apply(comps)
    bs.setup(a)


def cmd_check(a):
    comps = build_compositions(a.natoms, parse_k(a.k), a.ratios)
    apply(comps)
    bs.check(a)


def write_lammps(path, atoms, L):
    sy = atoms.get_chemical_symbols()
    with open(path, "w") as f:
        f.write(f"LAMMPS data file | AlCl3:urea MLMD start | {len(atoms)} atoms | types: 1 Al 2 C 3 Cl 4 H 5 N 6 O\n\n")
        f.write(f"{len(atoms)} atoms\n{len(TYPES)} atom types\n\n")
        f.write(f"0.0 {L:.6f} xlo xhi\n0.0 {L:.6f} ylo yhi\n0.0 {L:.6f} zlo zhi\n\nMasses\n\n")
        for i, e in enumerate(TYPES, 1):
            f.write(f"{i} {atomic_masses[atomic_numbers[e]]:.4f}  # {e}\n")
        f.write("\nAtoms # atomic\n\n")
        for i, (e, p) in enumerate(zip(sy, atoms.get_positions()), 1):
            f.write(f"{i} {TYPES.index(e) + 1} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")


def cmd_export(a):
    comps = build_compositions(a.natoms, parse_k(a.k), a.ratios)
    rows, bad = [], 0
    for r, c in comps.items():
        for s, target in c["seeds"].items():
            folder = os.path.join(a.outdir, r, s)
            xyz = os.path.join(folder, "packed.xyz")
            if not os.path.exists(xyz):
                print(f"{r}/{s}: packed.xyz missing (run packmol + check first)"); bad += 1; continue
            at = read(xyz)
            L = float(at.cell[0, 0])
            cnt = collections.Counter(at.get_chemical_symbols())
            nAl, nU = cnt["Al"], cnt["C"]
            ratio_ok = Fraction(nAl, nU) == Fraction(*RATIOS[r]) and cnt["Cl"] == 3 * nAl and cnt["N"] == 2 * nU \
                and cnt["O"] == nU and cnt["H"] == 4 * nU and nAl == c["nAl"] and nU == c["nU"]
            i, j, _ = bs.find_bonds(at)
            ncomp, lab = bs.components(len(at), i, j)
            census = collections.Counter()
            adj = collections.defaultdict(list)
            for x, y in zip(i, j):
                adj[x].append((y, None))
            syms = at.get_chemical_symbols()
            for k in range(ncomp):
                idx = list(np.where(lab == k)[0])
                census[bs.label([syms[q] for q in idx], idx, adj, syms)[0]] += 1
            census_ok = census == collections.Counter(target)
            d = at.get_all_distances(mic=True)
            mask = lab[:, None] != lab[None, :]
            dmin = d[mask].min()
            write_lammps(os.path.join(folder, "start.data"), at, L)
            rho = sum(atomic_masses[atomic_numbers[e]] for e in syms) / bs.NA / (L ** 3 * 1e-24)
            ok = ratio_ok and census_ok
            bad += not ok
            rows.append(dict(box=f"{r}/{s}", r=RATIOS[r][0] / RATIOS[r][1], nAl=nAl, nUrea=nU, natoms=len(at), L_A=round(L, 4),
                             rho_gcm3=round(rho, 4), min_intermol_dist_A=round(float(dmin), 3),
                             trained_composition=r in TRAINED, ratio_exact=ratio_ok, census_ok=census_ok, species=" ".join(f"{k}:{v}" for k, v in sorted(census.items()))))
            print(f"{r}/{s:10s} {'OK ' if ok else 'FAIL'} {len(at)} atoms  Al:U = {nAl}:{nU}  L = {L:.3f}  min inter-molecular d = {dmin:.2f} A")
    if rows:
        with open(os.path.join(a.outdir, "manifest.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        with open(os.path.join(a.outdir, "README_boxes.md"), "w") as f:
            f.write(README)
    print("\nall boxes OK" if bad == 0 else f"\n{bad} box(es) need attention")


README = """# Caixas de MLMD, AlCl3:ureia (~1500 atomos)
Cada pasta `<r>/<semente>/` tem: `start.data` (LAMMPS, atom_style atomic, tipos 1 Al 2 C 3 Cl 4 H 5 N 6 O), `packed.xyz` (extxyz com a cela),
`packmol.inp`, `target.txt` (especies alvo). `manifest.csv` resume tudo (razao exata, L, densidade, menor distancia intermolecular, censo de especies).
Caixas cubicas e periodicas, empacotadas na densidade experimental a 333 K (r=1,3 e provisoria). ESTAS GEOMETRIAS NAO ESTAO EQUILIBRADAS.
Ordem dos elementos no pair_coeff do MACE tem de seguir os tipos acima.
Protocolo sugerido (com o MACE treinado): minimize -> NVT curto com dt pequeno e rampa de T -> NPT para a densidade -> producao NVT.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("-o", "--outdir", default="mlmd_boxes")
        p.add_argument("--natoms", type=int, default=1500, help="target atoms per box")
        p.add_argument("--k", nargs="*", help="force the multiplier, e.g. r1.0=126 r1.3=11")
        p.add_argument("--ratios", nargs="*", help="subset, e.g. r1.0 r1.5 (default: all 7)")
    p = sub.add_parser("plan"); common(p)
    s = sub.add_parser("setup"); common(s)
    s.add_argument("--species", default="species/pdb")
    s.add_argument("--tol", type=float, default=2.0); s.add_argument("--al-radius", type=float, default=1.8)
    s.add_argument("--anchor-r", type=float, default=2.0); s.add_argument("--seed", type=int, default=2026)
    s.add_argument("--packmol", default="packmol")
    c = sub.add_parser("check"); common(c)
    e = sub.add_parser("export"); common(e)
    a = ap.parse_args()
    {"plan": cmd_plan, "setup": cmd_setup, "check": cmd_check, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
