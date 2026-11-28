#!/usr/bin/env python3
"""Set up new AIMD runs (legacy protocol) for seeds that lack a run at temperature T.

  setup_aimd_runs.py --legacy <legacy_dir> --T 333 --template T333/r10_ion --ref-T T400 \
      -o runs/aimd-t333-v1 <seed>...

For each seed, <out>/<seed>/ gets:
  equil.inp, prod.inp  the template run's inputs; only the header comment, PROJECT and (box)
                       ABC change. Check: they must differ from <ref-T>/<seed>/ only in the
                       header comment and the TEMPERATURE line.
  init.xyz             <ref-T>/<seed>/init.xyz; check: byte-identical to the last frame of
                       01_geo/<seed>/<seed>-pos-1.xyz and to every other existing T*/<seed>/init.xyz.
  <seed>_eq-RESTART.wfn  01_geo/<seed>/<seed>-RESTART.wfn (initial guess, as the legacy script).
  submit.sh            the template's script; only job name, ID and the GEO path change, plus
                       one line that records the repo commit at job start.
  SETUP.json           commit, sources and sha256 of every file written.
Refuses a dirty repo and an existing <out>/<seed>. Python standard library only.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", REPO] + list(args), universal_newlines=True).strip()


def sub_once(text, pattern, repl, what):
    new, n = re.subn(pattern, repl, text, flags=re.M)
    if n != 1:
        sys.exit("{}: expected exactly one match, found {}".format(what, n))
    return new


def box_of(inp):
    with open(inp) as f:
        m = re.findall(r"^\s*ABC \[angstrom\]\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$", f.read(), re.M)
    if len(m) != 1 or len(set(m[0])) != 1:
        sys.exit("{}: expected one cubic ABC line, found {}".format(inp, m))
    return m[0][0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--legacy", required=True)
    ap.add_argument("--T", required=True, type=int)
    ap.add_argument("--template", required=True, help="e.g. T333/r10_ion (under 02_aimd)")
    ap.add_argument("--ref-T", required=True, help="e.g. T400: existing run of the same seed")
    ap.add_argument("-o", "--outdir", required=True)
    ap.add_argument("seeds", nargs="+")
    a = ap.parse_args()

    if git("status", "--porcelain"):
        sys.exit("repo has uncommitted changes: commit first (the run records the commit)")
    commit = git("rev-parse", "HEAD")
    aimd = os.path.join(a.legacy, "02_aimd")
    tdir = os.path.join(aimd, a.template)
    tid = os.path.basename(tdir)
    if not re.fullmatch(r"T(\d+)", os.path.basename(os.path.dirname(tdir))) or \
            int(os.path.basename(os.path.dirname(tdir))[1:]) != a.T:
        sys.exit("template {} is not at T = {}".format(a.template, a.T))

    for seed in a.seeds:
        ref = os.path.join(aimd, a.ref_T, seed)
        geo = os.path.join(a.legacy, "01_geo", seed)
        dst = os.path.join(a.outdir, seed)
        if os.path.exists(dst):
            sys.exit("{} exists: not overwritten".format(dst))
        if glob.glob(os.path.join(aimd, "T{}".format(a.T), seed)):
            sys.exit("{}: a T{} run already exists in the legacy dir".format(seed, a.T))
        L = box_of(os.path.join(ref, "prod.inp"))
        written, sources = {}, {}

        # inputs
        texts = {}
        for name, proj in (("equil.inp", seed + "_eq"), ("prod.inp", seed)):
            src = os.path.join(tdir, name)
            sources[name] = {"path": src, "sha256": sha256(src)}
            with open(src) as f:
                t = f.read()
            t = sub_once(t, r"^# {} —".format(re.escape(tid)), "# {} —".format(seed), name + " comment")
            t = sub_once(t, r"^  PROJECT .*$", "  PROJECT {}".format(proj), name + " PROJECT")
            t = sub_once(t, r"^(\s*ABC \[angstrom\]).*$", r"\1 {0} {0} {0}".format(L), name + " ABC")
            if len(re.findall(r"^\s*TEMPERATURE {}\s*$".format(a.T), t, re.M)) != 1:
                sys.exit("{}: TEMPERATURE {} not found once".format(name, a.T))
            # compare with the same seed at ref-T: only comment and TEMPERATURE may differ
            with open(os.path.join(ref, name)) as f:
                r = f.read().splitlines()
            new = t.splitlines()
            if len(r) != len(new):
                sys.exit("{} {}: line count differs from {}".format(seed, name, a.ref_T))
            diff = [k for k, (x, y) in enumerate(zip(new, r)) if x != y]
            ok = all(k == 0 or re.match(r"^\s*TEMPERATURE ", new[k]) for k in diff)
            if not ok or len(diff) != 2:
                sys.exit("{} {}: differs from {} beyond comment/TEMPERATURE: lines {}".format(
                    seed, name, a.ref_T, [k + 1 for k in diff]))
            texts[name] = t

        # start structure
        with open(os.path.join(geo, seed + "-pos-1.xyz")) as f:
            lines = f.readlines()
        n = int(lines[0])
        last = "".join(lines[-(n + 2):]).encode()
        init_src = os.path.join(ref, "init.xyz")
        with open(init_src, "rb") as f:
            init = f.read()
        if init != last:
            sys.exit("{}: {}/init.xyz is not the last GEO_OPT frame".format(seed, a.ref_T))
        for other in glob.glob(os.path.join(aimd, "T*", seed, "init.xyz")):
            with open(other, "rb") as f:
                if f.read() != init:
                    sys.exit("{}: {} differs from {}".format(seed, other, init_src))
        if not any("GEOMETRY OPTIMIZATION COMPLETED" in open(p).read() or
                   "MAXIMUM NUMBER OF OPTIMIZATION STEPS REACHED" in open(p).read()
                   for p in glob.glob(os.path.join(geo, "geo_*.out"))):
            sys.exit("{}: GEO_OPT not finished".format(seed))

        # submit script
        src = os.path.join(tdir, "submit.sh")
        sources["submit.sh"] = {"path": src, "sha256": sha256(src)}
        with open(src) as f:
            s = f.read()
        tag = "m{}_{}".format(a.T, seed.replace("_", ""))
        s = sub_once(s, r"^#SBATCH --job-name=.*$", "#SBATCH --job-name=" + tag, "job-name")
        s = sub_once(s, r"^ID=.*$", "ID=" + seed, "ID")
        s = sub_once(s, r"^GEO=.*$", "GEO=" + geo, "GEO")
        s = sub_once(s, r'^cd "\$SLURM_SUBMIT_DIR"$',
                     'cd "$SLURM_SUBMIT_DIR"\n'
                     'echo "$(date "+%F %T") job $SLURM_JOB_ID repo {} commit '
                     '$(git -C {} rev-parse HEAD 2>/dev/null || echo unknown)" >> commit_at_start.txt'
                     .format(REPO, REPO), "cd line")

        os.makedirs(dst)
        for name, t in texts.items():
            with open(os.path.join(dst, name), "w") as f:
                f.write(t)
        with open(os.path.join(dst, "submit.sh"), "w") as f:
            f.write(s)
        os.chmod(os.path.join(dst, "submit.sh"), 0o755)
        with open(os.path.join(dst, "init.xyz"), "wb") as f:
            f.write(init)
        sources["init.xyz"] = {"path": init_src, "sha256": sha256(init_src)}
        wfn_src = os.path.join(geo, seed + "-RESTART.wfn")
        shutil.copy2(wfn_src, os.path.join(dst, seed + "_eq-RESTART.wfn"))
        sources[seed + "_eq-RESTART.wfn"] = {"path": wfn_src, "sha256": sha256(wfn_src)}
        for name in sorted(os.listdir(dst)):
            written[name] = sha256(os.path.join(dst, name))
        meta = {"seed": seed, "T_K": a.T, "box_A": float(L), "template": tdir,
                "compared_with": ref, "repo_commit": commit,
                "script_sha256": sha256(os.path.abspath(__file__)),
                "created": datetime.datetime.now().isoformat(timespec="seconds"),
                "sources": sources, "written_sha256": written}
        with open(os.path.join(dst, "SETUP.json"), "w") as f:
            json.dump(meta, f, indent=1, sort_keys=True)
            f.write("\n")
        print("{}: L = {} A, {} atoms, inputs differ from {} only in comment + TEMPERATURE; "
              "init.xyz = last GEO frame; job {}".format(dst, L, n, a.ref_T, tag))


if __name__ == "__main__":
    main()
