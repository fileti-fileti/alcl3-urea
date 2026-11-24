#!/usr/bin/env python3
"""Write a checked Packmol box as a clean PDB, for transfer to the MLMD project (SDumont).

  export_box_pdb.py <box_dir> -o <out.pdb>

Input: <box_dir>/packed.xyz (written and census-checked by build_mlmd_boxes.py check),
<box_dir>/packmol.inp (structure order and counts) and the species PDBs it names.
Output PDB:
  - CRYST1 with the cubic box (L to 0.001 A), space group P 1;
  - one residue per molecule: resName and atom names from the species PDB, chain A,
    resSeq = molecule number in Packmol order; element symbol in columns 77-78;
  - whole molecules (unwrapped by minimum image from each molecule's first atom), so a
    few atoms lie slightly outside [0, L); wrap on conversion if the code needs it;
  - no CONECT records.
Self-check: the PDB is read back and must match packed.xyz atom by atom (same element,
same position modulo L within 0.0006 A, the PDB rounding). Python standard library only.
"""
import argparse
import os
import re
import sys

TOL = 0.0006


def species_pdb(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                el = line[76:78].strip() or "".join(c for c in line[12:16] if c.isalpha())
                rows.append((line[12:16], line[17:20].strip(), el.capitalize()))
    return rows


def structures(path):
    order, name = [], None
    with open(path) as f:
        for line in f:
            s = line.split()
            if s[:1] == ["structure"]:
                name = s[1]
            elif s[:1] == ["number"]:
                order.append((name, int(s[1])))
    return order


def read_extxyz(path):
    with open(path) as f:
        n = int(f.readline())
        comment = f.readline()
        m = re.search(r'Lattice="([^"]+)"', comment)
        lat = [float(x) for x in m.group(1).split()]
        L = lat[0]
        if any(abs(lat[k]) > 1e-9 for k in (1, 2, 3, 5, 6, 7)) or \
                abs(lat[4] - L) > 1e-9 or abs(lat[8] - L) > 1e-9:
            sys.exit("{}: cell is not cubic".format(path))
        sym, pos = [], []
        for _ in range(n):
            t = f.readline().split()
            sym.append(t[0])
            pos.append([float(x) for x in t[1:4]])
    return sym, pos, L


def mic(d, L):
    return d - L * round(d / L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("box_dir")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()

    sym, pos, L = read_extxyz(os.path.join(a.box_dir, "packed.xyz"))
    order = structures(os.path.join(a.box_dir, "packmol.inp"))
    out = ["REMARK   1 MLMD start box, not equilibrated; source {}".format(
        os.path.abspath(a.box_dir))[:80],
        "CRYST1{:9.3f}{:9.3f}{:9.3f}{:7.2f}{:7.2f}{:7.2f} {:<11s}{:4d}".format(
            L, L, L, 90.0, 90.0, 90.0, "P 1", 1)]
    k, mol = 0, 0
    for name, n in order:
        tmpl = species_pdb(os.path.join(a.box_dir, name))
        for _ in range(n):
            mol += 1
            x0 = pos[k]
            for (aname, resn, el) in tmpl:
                if sym[k] != el:
                    sys.exit("atom {}: packed.xyz has {}, {} expects {}".format(k + 1, sym[k], name, el))
                p = [x0[c] + mic(pos[k][c] - x0[c], L) for c in range(3)]
                out.append("HETATM{:5d} {:4s} {:>3s} A{:4d}    {:8.3f}{:8.3f}{:8.3f}{:6.2f}{:6.2f}"
                           "          {:>2s}".format(k + 1, aname, resn, mol, p[0], p[1], p[2],
                                                     1.0, 0.0, el.upper()))
                k += 1
    if k != len(sym):
        sys.exit("packmol.inp accounts for {} atoms, packed.xyz has {}".format(k, len(sym)))
    out.append("END")
    with open(a.output, "w") as f:
        f.write("\n".join(out) + "\n")

    # self-check: read back
    back = []
    Lb = None
    with open(a.output) as f:
        for line in f:
            if line.startswith("CRYST1"):
                Lb = float(line[6:15])
            elif line.startswith("HETATM"):
                back.append((line[76:78].strip().capitalize(),
                             [float(line[30:38]), float(line[38:46]), float(line[46:54])]))
    worst = max(abs(mic(pb[c] - pa[c], L)) for (eb, pb), pa in zip(back, pos) for c in range(3))
    ok = len(back) == len(sym) and all(eb == s for (eb, _), s in zip(back, sym)) and \
        worst <= TOL and abs(Lb - L) <= 0.0005
    print("{}: {} atoms, {} molecules, L = {:.3f} A; read-back max |dx| mod L = {:.4f} A: {}".format(
        a.output, len(back), mol, Lb, worst, "OK" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
