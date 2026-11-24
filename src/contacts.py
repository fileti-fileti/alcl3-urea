#!/usr/bin/env python3
"""Intermolecular contacts per element pair: AIMD reference, Packmol radii, box check.

Molecules are the connected components of the bond graph of `extract_species.find_bonds`
(the criterion of the species census, SI S2.2). Two atoms are intermolecular when they lie
in different components; a contact is an intermolecular pair closer than RCUT.

  contacts.py ref <aimd_run_dir>... -o <ref.json>
      production frames of each run (reader of rdf.py); per pair: smallest distance seen
      (dmin, with run and step), percentiles of the per-frame minimum, number of contacts.
  contacts.py radii <ref.json> [-o <radii.json>]
      Packmol radius per element, the smallest (contact-weighted) set with
      R_a + R_b >= dmin_ab for every pair seen in the reference (linear program).
  contacts.py box <ref.json> <packed.xyz>...
      per pair: smallest distance in the box and the number of contacts below the
      reference dmin. A box passes when no contact is below dmin.

Needs ase, numpy, scipy: call an env's python explicitly (e.g. deepmd_intel) with -I.
"""
import argparse
import datetime
import itertools
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rdf  # noqa: E402  (read_xyz, aimd_inputs, sha256, repo_state)

RCUT = 5.0                      # A, contacts considered
ELEMENTS = ["Al", "C", "Cl", "H", "N", "O"]
VERSION = 1


def pair_key(a, b):
    return "-".join(sorted((a, b)))


PAIRS = [pair_key(a, b) for a, b in itertools.combinations_with_replacement(ELEMENTS, 2)]


def frame_contacts(symbols, positions, L):
    """{pair: array of intermolecular distances < RCUT} for one cubic periodic frame."""
    from ase import Atoms
    from ase.neighborlist import neighbor_list
    from extract_species import components, find_bonds
    atoms = Atoms(symbols, positions=positions, cell=[L, L, L], pbc=True)
    bi, bj, _ = find_bonds(atoms)
    _, lab = components(len(atoms), bi, bj)
    i, j, d = neighbor_list("ijd", atoms, RCUT)
    keep = (i < j) & (lab[i] != lab[j])
    i, j, d = i[keep], j[keep], d[keep]
    sym = np.asarray(symbols)
    keys = np.array([pair_key(a, b) for a, b in zip(sym[i], sym[j])])
    return {p: d[keys == p] for p in PAIRS if (keys == p).any()}, lab


def cmd_ref(a):
    commit, dirty = rdf.repo_state()
    if dirty:
        sys.exit("src/ has uncommitted changes: commit before computing (record the commit)")
    per_pair = {p: {"frame_min": [], "n": 0, "dmin": np.inf, "where": None} for p in PAIRS}
    sources, runs = [], []
    for run_dir in a.run_dirs:
        paths, L = rdf.aimd_inputs(run_dir)
        el, frames, n_read = rdf.read_xyz(paths)
        steps = sorted(frames)
        if steps != rdf.AIMD_STEPS:
            sys.exit("{}: steps {}..{} ({} unique), not 0..10000 every 10".format(
                run_dir, steps[0], steps[-1], len(steps)))
        name = os.path.basename(os.path.normpath(run_dir))
        T = os.path.basename(os.path.dirname(os.path.normpath(run_dir)))
        tag = "{}.{}".format(name, T)
        runs.append({"run": tag, "dir": os.path.abspath(run_dir), "L_A": L, "frames": len(steps)})
        sources += [{"path": os.path.abspath(p), "sha256": rdf.sha256(p)} for p in paths]
        for s in steps:
            con, _ = frame_contacts(list(el), frames[s], L)
            for p, d in con.items():
                q = per_pair[p]
                m = float(d.min())
                q["frame_min"].append(m)
                q["n"] += len(d)
                if m < q["dmin"]:
                    q["dmin"], q["where"] = m, {"run": tag, "step": s}
        print("{}: {} frames, L = {} A".format(tag, len(steps), L))
    out = {}
    for p, q in per_pair.items():
        if not q["frame_min"]:
            out[p] = {"seen": False}
            continue
        fm = np.array(q["frame_min"])
        out[p] = {"seen": True, "dmin_A": round(q["dmin"], 4), "where": q["where"],
                  "frames_with_contact": len(fm), "n_contacts": q["n"],
                  "frame_min_p01_A": round(float(np.percentile(fm, 1)), 4),
                  "frame_min_p50_A": round(float(np.percentile(fm, 50)), 4)}
    meta = {"contacts_version": VERSION, "rcut_A": RCUT, "runs": runs, "pairs": out,
            "sources": sources, "repo_commit": commit,
            "script_sha256": rdf.sha256(os.path.abspath(__file__)),
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "definition": "intermolecular = different components of the extract_species bond "
                          "graph in that frame; dmin = smallest such distance over all frames"}
    with open(a.output, "w") as f:
        json.dump(meta, f, indent=1, sort_keys=True)
        f.write("\n")
    print_ref(out)
    print("wrote", a.output)


def print_ref(out):
    print("{:6s} {:>8s} {:>9s} {:>9s} {:>10s}  {}".format(
        "pair", "dmin", "fmin_p01", "fmin_p50", "contacts", "dmin at"))
    for p in PAIRS:
        q = out[p]
        if not q["seen"]:
            print("{:6s} none within {} A".format(p, RCUT))
            continue
        print("{:6s} {:8.3f} {:9.3f} {:9.3f} {:10d}  {} step {}".format(
            p, q["dmin_A"], q["frame_min_p01_A"], q["frame_min_p50_A"], q["n_contacts"],
            q["where"]["run"], q["where"]["step"]))


def solve_radii(ref, margin=0.0):
    from scipy.optimize import linprog
    seen = [p for p in PAIRS if ref["pairs"][p]["seen"]]
    total = float(sum(ref["pairs"][p]["n_contacts"] for p in seen))
    A, b, c = [], [], np.zeros(len(ELEMENTS))
    for p in seen:
        x, y = p.split("-")
        row = np.zeros(len(ELEMENTS))
        row[ELEMENTS.index(x)] += 1
        row[ELEMENTS.index(y)] += 1
        A.append(-row)
        b.append(-ref["pairs"][p]["dmin_A"])
        c += row * ref["pairs"][p]["n_contacts"] / total
    res = linprog(c, A_ub=np.array(A), b_ub=np.array(b), bounds=[(0, None)] * len(ELEMENTS),
                  method="highs")
    if not res.success:
        sys.exit("linear program failed: " + res.message)
    radii = {e: round(float(np.ceil((r + margin) * 1000) / 1000), 3)
             for e, r in zip(ELEMENTS, res.x)}
    return radii, seen


def cmd_radii(a):
    with open(a.ref) as f:
        ref = json.load(f)
    radii, seen = solve_radii(ref, a.margin)
    print("margin per radius: {} A".format(a.margin))
    print("radii (A): " + "  ".join("{}={}".format(e, radii[e]) for e in ELEMENTS))
    print("{:6s} {:>8s} {:>8s} {:>7s}".format("pair", "dmin", "Ra+Rb", "excess"))
    for p in seen:
        x, y = p.split("-")
        s = radii[x] + radii[y]
        print("{:6s} {:8.3f} {:8.3f} {:7.3f}".format(p, ref["pairs"][p]["dmin_A"], s,
                                                     s - ref["pairs"][p]["dmin_A"]))
    if a.output:
        with open(a.output, "w") as f:
            json.dump({"radii_A": radii, "ref": os.path.abspath(a.ref), "margin_A": a.margin,
                       "rule": "min sum_pairs w_ab (R_a + R_b), w = contact fraction, "
                               "s.t. R_a + R_b >= dmin_ab; plus margin per radius; "
                               "rounded up to 0.001 A"}, f, indent=1)
            f.write("\n")
        print("wrote", a.output)


def cmd_box(a):
    from ase.io import read
    with open(a.ref) as f:
        ref = json.load(f)["pairs"]
    bad_boxes = 0
    for path in a.boxes:
        at = read(path)
        L = float(at.cell[0, 0])
        if not np.allclose(at.cell.array, np.diag([L, L, L])):
            sys.exit("{}: cell is not cubic".format(path))
        con, lab = frame_contacts(at.get_chemical_symbols(), at.get_positions(), L)
        print("\n== {}  ({} atoms, {} molecules, L = {:.4f} A)".format(
            path, len(at), lab.max() + 1, L))
        print("{:6s} {:>8s} {:>9s} {:>9s} {:>8s} {:>9s}".format(
            "pair", "box_min", "aimd_dmin", "fmin_p50", "n<dmin", "contacts"))
        nbad = 0
        for p in PAIRS:
            if p not in con:
                continue
            d = con[p]
            r = ref[p]
            dmin = r["dmin_A"] if r["seen"] else RCUT
            below = int((d < dmin).sum())
            nbad += below
            print("{:6s} {:8.3f} {:9.3f} {:>9s} {:8d} {:9d}{}".format(
                p, d.min(), dmin, "{:.3f}".format(r["frame_min_p50_A"]) if r["seen"] else "-",
                below, len(d), "  <-- below AIMD" if below else ""))
        print("RESULT {}: {}".format(path, "PASS (no contact below the AIMD minimum)" if nbad == 0
                                     else "FAIL ({} contacts below the AIMD minimum)".format(nbad)))
        bad_boxes += nbad > 0
    sys.exit(1 if bad_boxes else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("ref")
    r.add_argument("run_dirs", nargs="+")
    r.add_argument("-o", "--output", required=True)
    x = sub.add_parser("radii")
    x.add_argument("ref")
    x.add_argument("-o", "--output")
    x.add_argument("--margin", type=float, default=0.0,
                   help="A added to every radius (Packmol meets distances to ~0.01 A)")
    b = sub.add_parser("box")
    b.add_argument("ref")
    b.add_argument("boxes", nargs="+")
    a = ap.parse_args()
    if a.cmd is None:
        ap.error("choose ref, radii or box")
    {"ref": cmd_ref, "radii": cmd_radii, "box": cmd_box}[a.cmd](a)


if __name__ == "__main__":
    main()
