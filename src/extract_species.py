#!/usr/bin/env python3
"""
extract_species.py
------------------
Identify and extract the chemical species present in AlCl3:urea configurations
(e.g. the SI starting configurations of Carrasco-Busturia et al., ChemSusChem
2021, 14, 2034) and save one PDB (+ XYZ) per unique species.

Connectivity criterion (same as the paper):
    bond i-j if d_ij < r_i + r_j
    r(Al)=1.0, r(Cl)=1.7, r(O)=r(N)=r(C)=1.0, r(H)=0.37 Angstrom
    Cl is only allowed to bond to Al.

Periodic boundaries:
    - If the .xyz has a cell (extended XYZ, Lattice="..."), it is used.
    - Otherwise a cubic cell is built from the density (g/cm3):
        P4, P5 -> 1.5398 (1:1 mixture); everything else -> 1.5921 (1.5:1),
      or from --cell L / --density rho given on the command line.
    - --nopbc treats the configuration as non-periodic.
    Molecules cut by the box are made whole by following bonds (minimum image).

Usage:
    python extract_species.py ~/Downloads/S.I/Starting_Configuration_Model_*.xyz -o species
Outputs:
    species/pdb/<name>.pdb   one file per unique species (first instance found)
    species/xyz/<name>.xyz   same geometry, plain XYZ (handy for CREST/ORCA/CP2K)
    species/report.txt       species census per model + Al coordination numbers
Naming:
    U = urea; charge suffix _p (+1), _m (-1), _2p, _2m ...
    multi-Al species with >=2 ureas get an isomer tag: _iso2-0 = both ureas on the
    same Al ("same" in the paper), _iso1-1 = one urea per Al ("diff").
Requires: ase, numpy, scipy
"""
import argparse
import collections
import os
import re
import sys

import numpy as np
from ase.io import read
from ase.neighborlist import neighbor_list
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

RADII = {"Al": 1.0, "Cl": 1.7, "O": 1.0, "N": 1.0, "C": 1.0, "H": 0.37}
NA = 6.02214076e23
DENSITY_BY_MODEL = {"P4": 1.5398, "P5": 1.5398}  # 1:1 mixtures
DENSITY_DEFAULT = 1.5921                          # 1.5:1 mixtures
C_PER_LIGAND = 1                                  # urea: 1 C; acetamide would be 2

RESNAMES = {
    "urea": "URE", "AlCl3": "AL3", "Al2Cl6": "A26", "AlCl4_m": "AL4",
    "Al2Cl7_m": "A27", "AlCl3U": "AU1", "AlCl2U2_p": "AU2", "AlCl2U_p": "AUP",
    "Al2Cl6U": "A6U", "Al2Cl5U2_p_iso2-0": "A5S", "Al2Cl5U2_p_iso1-1": "A5D",
}


def model_tag(path):
    m = re.search(r"Model_([A-Za-z0-9]+)\.xyz$", os.path.basename(path))
    return m.group(1) if m else os.path.splitext(os.path.basename(path))[0]


def setup_cell(atoms, tag, args):
    if args.nopbc:
        atoms.pbc = False
        return "non-periodic (--nopbc)"
    if atoms.cell.volume > 1e-6 and args.cell is None:
        atoms.pbc = True
        return f"cell from file: {np.round(atoms.cell.lengths(), 3).tolist()} A"
    if args.cell is not None:
        L = args.cell
        src = f"cubic L = {L:.3f} A (--cell)"
    else:
        rho = args.density or DENSITY_BY_MODEL.get(tag, DENSITY_DEFAULT)
        vol = atoms.get_masses().sum() / NA / rho * 1e24  # A^3
        L = vol ** (1.0 / 3.0)
        src = f"cubic L = {L:.3f} A from rho = {rho} g/cm3"
    atoms.set_cell([L, L, L])
    atoms.pbc = True
    span = np.ptp(atoms.positions, axis=0)
    if np.any(span > 1.5 * L):
        src += f"  [WARNING: coordinate span {np.round(span, 1).tolist()} >> L; cell guess may be wrong]"
    return src


def find_bonds(atoms):
    sym = np.array(atoms.get_chemical_symbols())
    unknown = set(sym) - set(RADII)
    if unknown:
        sys.exit(f"Unknown elements {unknown}: add them to RADII.")
    r = np.array([RADII[s] for s in sym])
    i, j, d, D = neighbor_list("ijdD", atoms, 2 * max(RADII.values()))
    ok = (d < r[i] + r[j]) & (i != j)
    cl_i, cl_j = sym[i] == "Cl", sym[j] == "Cl"
    ok &= (~cl_i & ~cl_j) | (cl_i & (sym[j] == "Al")) | (cl_j & (sym[i] == "Al"))
    return i[ok], j[ok], D[ok]


def components(n, i, j):
    g = coo_matrix((np.ones(len(i)), (i, j)), shape=(n, n))
    return connected_components(g, directed=False)


def make_whole(atoms, idx, adj):
    """Unwrap one fragment by walking its bond graph with minimum-image vectors."""
    pos = {idx[0]: atoms.positions[idx[0]].copy()}
    queue = [idx[0]]
    while queue:
        a = queue.pop()
        for b, vec in adj[a]:
            if b not in pos:
                pos[b] = pos[a] + vec
                queue.append(b)
    return np.array([pos[k] for k in idx])


def label(syms, idx, adj, atom_sym):
    c = collections.Counter(syms)
    n_al, n_cl, n_c = c.get("Al", 0), c.get("Cl", 0), c.get("C", 0)
    n_u = n_c // C_PER_LIGAND
    charge = 3 * n_al - n_cl  # formal charges: Al +3, Cl -1, ligand 0
    odd = not (c.get("O", 0) == n_u and c.get("N", 0) == 2 * n_u and c.get("H", 0) == 4 * n_u)
    if n_al == 0 and n_cl == 0:
        name = "urea" if n_u == 1 else f"U{n_u}"
    else:
        name = "Al" + (str(n_al) if n_al > 1 else "") + "Cl" + (str(n_cl) if n_cl > 1 else "")
        if n_u:
            name += "U" + (str(n_u) if n_u > 1 else "")
    if charge:
        name += {1: "_p", -1: "_m", 2: "_2p", -2: "_2m"}.get(charge, f"_q{charge}")
    if n_al >= 2 and n_u >= 2:
        per_al = []
        for a in idx:
            if atom_sym[a] == "Al":
                per_al.append(sum(1 for b, _ in adj[a] if atom_sym[b] == "O"))
        name += "_iso" + "-".join(str(x) for x in sorted(per_al, reverse=True))
    if odd:
        name += "_ODD"  # ligand atoms do not add up to whole ureas: inspect it
    return name, charge


def write_pdb(fname, syms, pos, bonds_local, resname, title):
    pos = pos - pos.mean(axis=0)
    count = collections.Counter()
    out = [f"TITLE     {title}", "REMARK   1 generated by extract_species.py"]
    for k, (s, p) in enumerate(zip(syms, pos), start=1):
        count[s] += 1
        name = f"{s.upper()}{count[s]}"[:4]
        out.append(f"HETATM{k:5d} {name:<4s} {resname:>3s} A{1:4d}    "
                   f"{p[0]:8.3f}{p[1]:8.3f}{p[2]:8.3f}{1.0:6.2f}{0.0:6.2f}"
                   f"          {s.upper():>2s}")
    nb = collections.defaultdict(set)
    for a, b in bonds_local:
        nb[a + 1].add(b + 1)
        nb[b + 1].add(a + 1)
    for a in sorted(nb):
        partners = sorted(nb[a])
        for s in range(0, len(partners), 4):
            out.append(f"CONECT{a:5d}" + "".join(f"{b:5d}" for b in partners[s:s + 4]))
    out.append("END")
    with open(fname, "w") as f:
        f.write("\n".join(out) + "\n")
    return pos


def write_xyz(fname, syms, pos, comment):
    with open(fname, "w") as f:
        f.write(f"{len(syms)}\n{comment}\n")
        for s, p in zip(syms, pos):
            f.write(f"{s:2s} {p[0]:12.6f} {p[1]:12.6f} {p[2]:12.6f}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="input .xyz configurations")
    ap.add_argument("-o", "--outdir", default="species")
    ap.add_argument("--density", type=float, help="force density (g/cm3) for cells not in the file")
    ap.add_argument("--cell", type=float, help="force cubic cell edge (A)")
    ap.add_argument("--nopbc", action="store_true", help="treat configurations as non-periodic")
    ap.add_argument("--all", action="store_true", help="save every instance, not only the first")
    args = ap.parse_args()

    os.makedirs(os.path.join(args.outdir, "pdb"), exist_ok=True)
    os.makedirs(os.path.join(args.outdir, "xyz"), exist_ok=True)
    saved, report = {}, []
    extra_res = 0

    for path in args.files:
        tag = model_tag(path)
        atoms = read(path)
        cell_info = setup_cell(atoms, tag, args)
        sym = atoms.get_chemical_symbols()
        i, j, D = find_bonds(atoms)
        adj = collections.defaultdict(list)
        for a, b, v in zip(i, j, D):
            adj[a].append((b, v))
        ncomp, lab = components(len(atoms), i, j)

        census, al_cn = collections.Counter(), collections.Counter()
        for a, s in enumerate(sym):
            if s == "Al":
                al_cn[len(adj[a])] += 1
        for c in range(ncomp):
            idx = list(np.where(lab == c)[0])
            fsyms = [sym[a] for a in idx]
            name, charge = label(fsyms, idx, adj, sym)
            census[name] += 1
            if name in saved and not args.all:
                continue
            n_inst = saved.get(name, 0) + 1
            saved[name] = n_inst
            fname = name if n_inst == 1 else f"{name}_{n_inst}"
            pos = make_whole(atoms, idx, adj)
            loc = {g: k for k, g in enumerate(idx)}
            bonds_local = [(loc[a], loc[b]) for a, b in zip(i, j) if a in loc and b in loc and a < b]
            if name not in RESNAMES:
                extra_res += 1
                RESNAMES[name] = f"X{extra_res:02d}"
            title = f"{name} charge {charge:+d} from {os.path.basename(path)}"
            pos = write_pdb(os.path.join(args.outdir, "pdb", fname + ".pdb"),
                            fsyms, pos, bonds_local, RESNAMES[name], title)
            write_xyz(os.path.join(args.outdir, "xyz", fname + ".xyz"), fsyms, pos,
                      f"{name} charge={charge} source={os.path.basename(path)}")

        report.append(f"== {tag}  ({len(atoms)} atoms)  {cell_info}")
        for nm, n in sorted(census.items(), key=lambda x: (-x[1], x[0])):
            report.append(f"   {n:4d}  {nm}")
        report.append("   Al coordination numbers: " +
                      ", ".join(f"CN{k}: {v}" for k, v in sorted(al_cn.items())))
        report.append("")

    report.append("Saved species (resname):")
    for nm in sorted(saved):
        report.append(f"   {nm:24s} {RESNAMES[nm]}")
    text = "\n".join(report)
    with open(os.path.join(args.outdir, "report.txt"), "w") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
