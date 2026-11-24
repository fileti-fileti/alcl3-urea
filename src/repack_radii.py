#!/usr/bin/env python3
"""Rewrite a Packmol box input with one radius per element; everything else is kept.

  repack_radii.py <v1_box_dir> <v2_box_dir> --radii <radii.json>

Reads <v1_box_dir>/packmol.inp (written by build_seeds.setup), copies the species PDBs it
names and target.txt into <v2_box_dir>, and writes <v2_box_dir>/packmol.inp with:
  - the same structures, counts, ion anchors (`inside sphere`), Packmol seed and pbc box;
  - every atom given the radius of its element (radii.json from `contacts.py radii`),
    the anchored Al included; the old per-atom radius blocks are dropped;
  - `tolerance` set to twice the largest radius (it only sets the default radius, and
    every atom now has an explicit one).
Then run Packmol in <v2_box_dir> and `build_mlmd_boxes.py check/export` as for v1.
Python standard library only.
"""
import argparse
import json
import os
import shutil
import sys


def pdb_elements(path):
    el = []
    with open(path) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                e = line[76:78].strip() or "".join(c for c in line[12:16] if c.isalpha())
                el.append(e.capitalize())
    return el


def parse(path):
    """(header lines, [structure blocks as line lists])"""
    header, blocks, cur = [], [], None
    with open(path) as f:
        for raw in f:
            line = raw.rstrip("\n")
            s = line.strip()
            if s.startswith("structure "):
                cur = [s]
            elif s == "end structure":
                cur.append(s)
                blocks.append(cur)
                cur = None
            elif cur is not None:
                if s:
                    cur.append(s)
            elif s:
                header.append(s)
    return header, blocks


def rewrite_block(block, radii, src_dir):
    pdb = block[0].split()[1]
    el = pdb_elements(os.path.join(src_dir, pdb))
    out = [block[0]]
    anchor, k = None, 1
    while k < len(block) - 1:
        s = block[k]
        if s.startswith("atoms "):
            end = block.index("end atoms", k)
            inner = block[k + 1:end]
            spheres = [x for x in inner if x.startswith("inside ")]
            other = [x for x in inner if not x.startswith(("radius", "inside "))]
            if other:
                sys.exit("{}: unexpected line in atoms block: {}".format(pdb, other))
            if spheres:
                idx = [int(x) for x in s.split()[1:]]
                if len(idx) != 1 or anchor is not None:
                    sys.exit("{}: expected one anchored atom per structure".format(pdb))
                anchor = idx[0]
                out += ["  atoms {}".format(anchor),
                        "    radius {}".format(radii[el[anchor - 1]])] + \
                       ["    " + x for x in spheres] + ["  end atoms"]
            k = end + 1
        else:
            out.append("  " + s)
            k += 1
    for e in sorted(set(el)):
        idx = [i + 1 for i, x in enumerate(el) if x == e and i + 1 != anchor]
        if idx:
            out += ["  atoms " + " ".join(map(str, idx)), "    radius {}".format(radii[e]),
                    "  end atoms"]
    out.append("end structure")
    return pdb, out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--radii", required=True)
    a = ap.parse_args()
    with open(a.radii) as f:
        radii = json.load(f)["radii_A"]
    header, blocks = parse(os.path.join(a.src, "packmol.inp"))
    os.makedirs(a.dst, exist_ok=True)
    tol = 2 * max(radii.values())
    head = []
    for s in header:
        if s.startswith("tolerance"):
            head.append("tolerance {:.3f}".format(tol))
        elif s.startswith("#"):
            head.append(s + " | radii per element: " +
                        " ".join("{}={}".format(e, radii[e]) for e in sorted(radii)))
        else:
            head.append(s)
    body, pdbs = [], set()
    for b in blocks:
        pdb, lines = rewrite_block(b, radii, a.src)
        pdbs.add(pdb)
        body += lines + [""]
    for name in sorted(pdbs) + ["target.txt"]:
        shutil.copy2(os.path.join(a.src, name), os.path.join(a.dst, name))
    with open(os.path.join(a.dst, "packmol.inp"), "w") as f:
        f.write("\n".join(head) + "\n\n" + "\n".join(body))
    print("{}: {} structure blocks, species {}, tolerance {:.3f}".format(
        a.dst, len(blocks), sorted(pdbs), tol))


if __name__ == "__main__":
    main()
