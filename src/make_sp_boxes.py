#!/usr/bin/env python3
"""
make_sp_boxes.py -- single-point (ENERGY_FORCE) CP2K inputs for the large MLMD boxes, at the SAME level as the AIMD
sampling runs, and a report of energies/forces to judge how clashed the Packmol boxes are.

The FORCE_EVAL block is taken from an existing AIMD input (02_aimd/T*/<ID>/md.inp, i.e. what really ran), so the
level of theory (functional, D3, basis, cutoffs, EPS_SCF, SCF scheme, KIND blocks) is identical. Only these are changed:
cell (ABC), coordinates (init.xyz of the large box), SCF_GUESS RESTART -> ATOMIC, inner MAX_SCF (--max-scf),
and forces printing. Nothing else.

  python scripts/make_sp_boxes.py setup  -o 08_mlmd_boxes [--ref 02_aimd/T400/r15_neut/md.inp] [--node n12]
                                          [--max-scf 100] [--time 2-00:00:00] [--ratios r1.0 r1.5 ...]
  bash 08_mlmd_boxes/submit_sp.sh r1.0/neutro      # test ONE box first (measure time/memory), then:
  bash 08_mlmd_boxes/submit_sp.sh all
  python scripts/make_sp_boxes.py report -o 08_mlmd_boxes      # -> sp_report.csv + table

Per box:  <r>/<seed>/sp/{sp.inp, init.xyz, submit.sh}    output: sp.out
Slurm header, module, mpirun and ranks come from config.py (SLURM block: n12 = 112 ranks per job, 4 jobs side by side).
Run from the project root (the folder with config.py and 02_aimd/).
"""
import argparse, csv, glob, os, re, sys

from ase.io import read

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)
import config  # noqa: E402

HA_EV = 27.211386245988
HB_EVA = HA_EV / 0.529177210903


def find_ref(arg):
    if arg:
        return arg
    c = sorted(glob.glob(os.path.join(ROOT, "02_aimd", "T400", "*", "md.inp"))) or \
        sorted(glob.glob(os.path.join(ROOT, "02_aimd", "T*", "*", "md.inp")))
    if not c:
        sys.exit("no 02_aimd/T*/<ID>/md.inp found; pass --ref")
    return c[0]


def force_eval_block(ref):
    t = open(ref).read()
    i, j = t.index("&FORCE_EVAL"), t.rindex("&END FORCE_EVAL") + len("&END FORCE_EVAL")
    return t[i:j] + "\n"


def adapt(fe, L, max_scf):
    n_before = fe
    fe, n1 = re.subn(r"ABC\s*(\[[^\]]*\])?\s+\S+\s+\S+\s+\S+", f"ABC [angstrom] {L:.6f} {L:.6f} {L:.6f}", fe, count=1)
    fe, n2 = re.subn(r"COORD_FILE_NAME\s+\S+", "COORD_FILE_NAME init.xyz", fe, count=1)
    fe, n3 = re.subn(r"SCF_GUESS\s+\w+", "SCF_GUESS ATOMIC", fe, count=1)
    fe, n4 = re.subn(r"(&SCF\b.*?\n\s*MAX_SCF\s+)\d+", lambda m: m.group(1) + str(max_scf), fe, count=1, flags=re.S)
    fe, n5 = re.subn(r"(METHOD\s+QS\s*\n)", r"\1  &PRINT\n    &FORCES ON\n    &END FORCES\n  &END PRINT\n", fe, count=1)
    if not (n1 and n2 and n3 and n4 and n5):
        sys.exit(f"could not adapt the reference FORCE_EVAL (ABC {n1}, COORD {n2}, SCF_GUESS {n3}, MAX_SCF {n4}, PRINT {n5})")
    return fe


def slurm_seconds(t):
    days, hms = t.split("-") if "-" in t else ("0", t)
    h, m, s = (int(x) for x in hms.split(":"))
    return int(days) * 86400 + h * 3600 + m * 60 + s


def header(node):
    spec = config.SLURM["nodes"][node]
    part = [f"#SBATCH --partition={spec[2]}"] if len(spec) > 2 and spec[2] else []
    return "\n".join(config.SLURM["header"] + part + [f"#SBATCH --nodelist={node}", f"#SBATCH --ntasks={spec[0]}",
                                                      "#SBATCH --cpus-per-task=1"])


def cmd_setup(a):
    ref = find_ref(a.ref)
    fe0 = force_eval_block(ref)
    print(f"reference input: {os.path.relpath(ref, ROOT)}")
    for k in ("CUTOFF", "REL_CUTOFF", "EPS_SCF", "SCF_GUESS", "MAX_SCF", "MINIMIZER", "TYPE"):
        m = re.search(rf"\b{k}\s+(\S+)", fe0)
        print(f"   {k:11s} {m.group(1) if m else '-'}")
    S = config.SLURM
    if a.node not in S["nodes"]:
        sys.exit(f"node {a.node} not in config.SLURM['nodes']")
    wall = slurm_seconds(a.time) - 60 * S["cp2k_walltime_margin_min"]
    boxes = sorted(glob.glob(os.path.join(a.outdir, "r*", "*", "packed.xyz")))
    if a.ratios:
        boxes = [b for b in boxes if os.path.relpath(b, a.outdir).split(os.sep)[0] in a.ratios]
    if not boxes:
        sys.exit(f"no packed.xyz under {a.outdir}")
    names = []
    for xyz in boxes:
        d = os.path.dirname(xyz)
        name = os.path.relpath(d, a.outdir)                     # r1.0/neutro
        at = read(xyz)
        L = at.cell.lengths()
        if max(L) - min(L) > 1e-6:
            sys.exit(f"{name}: non-cubic cell {L}")
        sp = os.path.join(d, "sp"); os.makedirs(sp, exist_ok=True)
        with open(os.path.join(sp, "init.xyz"), "w") as f:
            f.write(f"{len(at)}\n{name} MLMD box, cubic L = {L[0]:.6f} A\n")
            for s, p in zip(at.get_chemical_symbols(), at.positions):
                f.write(f"{s:2s} {p[0]:14.8f} {p[1]:14.8f} {p[2]:14.8f}\n")
        proj = "sp_" + name.replace("/", "_").replace(".", "")
        inp = (f"# {name} - single point (ENERGY_FORCE), same level as the AIMD sampling runs\n"
               f"&GLOBAL\n  PROJECT {proj}\n  RUN_TYPE ENERGY_FORCE\n  PRINT_LEVEL MEDIUM\n  WALLTIME {wall}\n&END GLOBAL\n\n"
               + adapt(fe0, L[0], a.max_scf))
        open(os.path.join(sp, "sp.inp"), "w").write(inp)
        sub = (f"#!/bin/bash\n#SBATCH --job-name={proj[:14]}\n{header(a.node)}\n#SBATCH --time={a.time}\n"
               f"#SBATCH --output=slurm-%j.out\nset -e\ncd \"$SLURM_SUBMIT_DIR\"\nmodule load {S['module']}\n"
               f"export OMP_NUM_THREADS=${{SLURM_CPUS_PER_TASK:-1}}\n{S['mpirun']} {S['exe']} -i sp.inp -o sp.out\n")
        p = os.path.join(sp, "submit.sh"); open(p, "w").write(sub); os.chmod(p, 0o755)
        names.append(name)
    sub_all = ["#!/bin/bash", "# usage: bash submit_sp.sh <r/seed> | all    (e.g. r1.0/neutro)",
               'cd "$(dirname "$0")"', 'ARG="${1:?usage: bash submit_sp.sh <r/seed> | all}"', ""]
    for n in names:
        sub_all.append(f'[[ "$ARG" == all || "$ARG" == {n} ]] && {{ jid=$(cd {n}/sp && sbatch --parsable submit.sh); echo "{n:16s} $jid"; }} || true')
    p = os.path.join(a.outdir, "submit_sp.sh"); open(p, "w").write("\n".join(sub_all) + "\n"); os.chmod(p, 0o755)
    print(f"\n{len(names)} single-points written (node {a.node}, {S['nodes'][a.node][0]} ranks each, inner MAX_SCF {a.max_scf}, "
          f"time {a.time}).\nFIRST:  bash {a.outdir}/submit_sp.sh {names[0]}   (measure time and memory), then: bash {a.outdir}/submit_sp.sh all")


def parse_sp(path):
    t = open(path, errors="replace").read()
    r = {"E": None, "conv": False, "scf": None, "F": [], "el": []}
    m = re.findall(r"ENERGY\| Total FORCE_EVAL \( QS \) energy[^:\n]*:\s+(-?\d+\.\d+)", t)
    r["E"] = float(m[-1]) if m else None
    r["conv"] = "SCF run converged" in t and "SCF run NOT converged" not in t
    m = re.search(r"SCF run converged in\s+(\d+)", t)
    r["scf"] = int(m.group(1)) if m else None
    i = t.rfind("ATOMIC FORCES in [a.u.]")
    if i >= 0:
        for line in t[i:].splitlines()[1:]:
            if "SUM OF ATOMIC FORCES" in line:
                break
            p = line.split()
            if len(p) >= 6 and p[0].isdigit():
                try:
                    r["F"].append([float(x) * HB_EVA for x in p[-3:]]); r["el"].append(p[2])
                except ValueError:
                    pass
    return r


def cmd_report(a):
    import numpy as np
    rows = []
    for d in sorted(glob.glob(os.path.join(a.outdir, "r*", "*", "sp"))):
        name = os.path.relpath(os.path.dirname(d), a.outdir)
        out = os.path.join(d, "sp.out")
        if not os.path.exists(out):
            rows.append(dict(box=name, status="no output")); continue
        r = parse_sp(out)
        if r["E"] is None or not r["F"]:
            rows.append(dict(box=name, status="running or failed (no energy/forces)")); continue
        F = np.array(r["F"]); mag = np.linalg.norm(F, axis=1); el = np.array(r["el"])
        k = int(mag.argmax())
        row = dict(box=name, status="ok" if r["conv"] else "SCF NOT CONVERGED", natoms=len(F),
                   E_eV_per_atom=round(r["E"] * HA_EV / len(F), 4), scf_steps=r["scf"],
                   Fmax_eV_A=round(float(mag.max()), 2), Fmax_element=el[k], Frms_eV_A=round(float(np.sqrt((F ** 2).sum(1).mean())), 3),
                   n_above_5=int((mag > 5).sum()), n_above_10=int((mag > 10).sum()))
        for e in sorted(set(el)):
            row[f"Fmax_{e}"] = round(float(mag[el == e].max()), 2)
        rows.append(row)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(a.outdir, "sp_report.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print(f"{'box':16s} {'status':18s} {'E/atom(eV)':>11s} {'SCF':>4s} {'Fmax(eV/A)':>10s} {'on':>3s} {'Frms':>6s} {'>5':>4s} {'>10':>4s}")
    for r in rows:
        if r["status"] != "ok" and "Fmax_eV_A" not in r:
            print(f"{r['box']:16s} {r['status']}"); continue
        print(f"{r['box']:16s} {r['status']:18s} {r['E_eV_per_atom']:11.4f} {str(r['scf_steps']):>4s} {r['Fmax_eV_A']:10.2f} "
              f"{r['Fmax_element']:>3s} {r['Frms_eV_A']:6.3f} {r['n_above_5']:4d} {r['n_above_10']:4d}")
    print(f"\n-> {a.outdir}/sp_report.csv   (forces in eV/A; per-element Fmax in the csv)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup"); s.add_argument("-o", "--outdir", default="08_mlmd_boxes"); s.add_argument("--ref")
    s.add_argument("--node", default="n12"); s.add_argument("--max-scf", type=int, default=100)
    s.add_argument("--time", default="2-00:00:00"); s.add_argument("--ratios", nargs="*")
    r = sub.add_parser("report"); r.add_argument("-o", "--outdir", default="08_mlmd_boxes")
    a = ap.parse_args()
    {"setup": cmd_setup, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
