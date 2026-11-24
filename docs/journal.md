# Journal

Append-only. Newest entry first, directly below the marker line.
Title: `## YYYY-MM-DD — <machine> — <short title>`.

```
## YYYY-MM-DD — <machine> — <short title>
- Goal: ...
- Done: ... (each item with its commit hash and job ID)
- Results: the conclusion and the few numbers that carry it, linked to the doc
- Decisions: proposals with the owner's ok; ADRs added or changed (ADR-0017)
- Problems: what failed, with job IDs and error lines (root cause)
- Next: concrete steps
```

<!-- NEW ENTRIES BELOW -->

## 2026-11-24 — neumann — Check of the 08_mlmd_boxes copy; two sessions at once
- Goal: start-session; bring the 2026-11-21 work into the project (owner's request).
- Done:
  - The request had already been carried out by another session running at the same time
    (`23fa66e`, `bf437c6`, 06:18-06:22); nothing redone.
  - Independent check: 419 of the 420 files of `08_mlmd_boxes` are identical (sha256) in
    `data/boxes/mlmd-v1` + `runs/sp-boxes-v1`; the one left out is
    `r1.0/neutro/sp/sp_r10_neutro-RESTART.wfn`; the only file in the copies not in the
    original is `runs/sp-boxes-v1/sp_report.csv`. The 5 scripts in `src/` are identical to
    those in `~/alcl3_urea_data/scripts/` (`cmp`).
  - Ledger: `cost_ledger.py add`: 0 rows; 6 ended jobs outside the project skipped
    (Eudes-Jordan, hidrotopia-co2).
- Results: job 4401: CP2K total time 2973.96 s (`sp.out`, line `CP2K 1 1.0`); sacct
  Elapsed 2981 s. Energy, ranks, node and forces as in the 2026-11-21 entry.
- Decisions: none.
- Problems:
  - Two Claude sessions worked in this repo at the same time; this one found the task done
    only by reading `git log`. Risk of conflicting commits.
  - GitHub origin still unreachable: `git ls-remote origin` gives "Repository not found";
    `ssh -T git@github-alcl3-urea` greets `fileti-fileti/alcl3-urea-`.
- Next: owner fixes the GitHub repo name, then `git push -u origin main`; one session per
  repo at a time.

## 2026-11-24 — neumann — MLMD boxes into the project; GitHub never pushed
- Goal: find the large boxes, bring the 2026-11-21 work into the project, close the session.
- Done:
  - Searched `~` (names, and contents of ~12.9k structure/input files): Al exists only in
    `~/alcl3_urea_data`; the only large boxes are its `08_mlmd_boxes`; the only GEO_OPT
    inputs are the 15 seeds in `01_geo` (396-432 atoms). No geopt of the large boxes on
    neumann.
  - Copied `08_mlmd_boxes` (original untouched) to `data/boxes/mlmd-v1` (311 files: boxes,
    manifest, README, Packmol inputs and logs) and `runs/sp-boxes-v1` (108 files:
    `submit_sp.sh`, `*/*/sp/`; the 361 MB `.wfn` restart left out); sha256 of every copied
    file matches the original.
  - `23fa66e`: `build_mlmd_boxes.py`, `make_sp_boxes.py` and their imports (`build_seeds.py`,
    `extract_species.py`, `config.py`) into `src/`, verbatim; `make_sp_boxes.py report -o
    runs/sp-boxes-v1` (deepmd_intel env) reproduces job 4401.
  - Ledger: jobs 4400 and 4401 added with `--jobs` (submitted outside `runs/`).
  - `CLAUDE.md`: data line (project copies are the live ones); confidentiality line allows
    the private GitHub origin.
- Results: none registered (the SP test supports no claim).
- Decisions (owner's ok, 2026-11-24): copy, not move, `08_mlmd_boxes` into the project,
  without the `.wfn`; the legacy dir stays read-only. Code, docs and derived results may go
  to the private GitHub origin.
- Problems:
  - GitHub origin never pushed: no `origin/*` ref; the deploy key `~/.ssh/github_alcl3-urea`
    reaches `fileti-fileti/alcl3-urea-` (trailing hyphen, `ssh -T` greeting), which is
    empty; `git ls-remote origin` gives "Repository not found". The 2026-11-18 status line
    "pushed to origin" was wrong. Unchanged after the owner reported the rename.
  - The 2026-11-21 work was done in the legacy dir, outside the repo, with no record until
    today; no session transcript of it on neumann.
- Next: owner fixes the GitHub repo name, then `git push -u origin main`; decide the other 34
  single points vs MACE minimisation; adapt `src/make_sp_boxes.py` (status block, Later).

## 2026-11-21 — neumann — MLMD boxes and single-point test (recorded 2026-11-24)
- Goal: ~1500-atom boxes for MLMD, and a CP2K single point to see how clashed they are.
- Done (in `~/alcl3_urea_data`, outside the repo; reconstructed on 2026-11-24 from the
  files, their times and sacct):
  - `scripts/build_mlmd_boxes.py` → `08_mlmd_boxes/`: 35 cubic boxes, r in {1.0, 1.2, 1.3,
    1.4, 1.5, 1.6, 1.7} x 5 seeds (r1.0: reagentes, neutro, ionico, misto, fora_eq; others:
    reagentes, neutro, ionicoA, ionicoB, misto), 1428-1536 atoms, Packmol at the
    experimental density at 333 K (r = 1.3 provisional), not equilibrated; `manifest.csv`
    (L, density, min intermolecular distance, census). r 1.2, 1.4, 1.6, 1.7 (20 boxes):
    `trained_composition=False`.
  - `scripts/make_sp_boxes.py setup` → 35 ENERGY_FORCE inputs, FORCE_EVAL copied from an AIMD
    `md.inp` (which one: unknown): CUTOFF 350 / REL_CUTOFF 50, EPS_SCF 1e-6, OT DIIS,
    SCF_GUESS ATOMIC, MAX_SCF 100 x 20 outer; CP2K module cp2k/2024.1-gcc-12.2.0-iy4ur5k.
  - Jobs 4400 (FAILED) and 4401 (COMPLETED), both r1.0/neutro; the other 34 not submitted.
- Results: job 4401 (n12, 112 ranks, 2981 s, 92.7422 core-hours): SCF converged in outer
  cycle 2 (189 steps; the first inner loop stopped at 100); E = -11485.838865 Ha
  (-206.7101 eV/atom); |F| max 9.64 eV/A (Cl), rms 2.529 eV/A, 134 atoms above 5 eV/A,
  none above 10 (`make_sp_boxes.py report`).
- Problems: job 4400 failed at start, partition `batch`, no node assigned. `config.py` puts
  `--partition=batch` with `--nodelist=n12` (n12 is in `EPYC_9734`); the 35 `submit.sh` carry
  `EPYC_9734` and were rewritten at 13:22, after the failure (cause inferred from sacct and
  file times; the job log was not kept).
- Next: see 2026-11-24.

## 2026-11-18 — neumann — Project start
- Goal: create alcl3-urea from lab-template and record the interview.
- Done:
  - `~/alcl3-urea` cloned from lab-template `24e4016`; `origin` = GitHub
    `fileti-fileti/alcl3-urea` (private; deploy key `~/.ssh/github_alcl3-urea`, ssh alias
    `github-alcl3-urea`); remote `template`; pre-commit hook on; store
    `~/alcl3-urea-store/{data,runs,logs}`; tests 52 OK.
  - Ledger: 104 ended jobs submitted under `~/alcl3_urea_data` since 2026-10-13 added with
    `--workdir` (GEO_OPT, AIMD, convergence tests; failed and cancelled included):
    145219.4400 core-hours. The jobs run on SDumont are not in it.
  - Interview: question and set-up from the SI draft v0.3 (2026-10-14) and the dataset
    report for Davi (2026-10-24); legacy dir read-only (ADR-0008), frame pool onward in
    this repo; confidential (unpublished).
  - Legacy dir (read-only look; no output analysed): 20 of 30 AIMD runs have `DONE` on
    neumann; the 10 without are those run on SDumont with CP2K 2024.3 (T333 r13_ionB,
    r15_ionA, r15_ionB, r15_mist; T450 r10_fora, r10_neut, r10_reag, r13_neut, r15_neut,
    r15_reag). Convergence stages A, B, D ended 2026-10-26 (jobs 4250-4261); C and E not
    run. `conv_test/sp_template.inp`: PBE-D3(BJ)/DZVP-MOLOPT-SR-GTH, CUTOFF 1000, REL_CUTOFF
    60, EPS_SCF 1e-7, analytical stress. `03_pool` to `07_external` and `inbox/` empty.
- Results: none.
- Decisions: legacy dir read-only, frame pool onward in this repo; legacy jobs charged with
  `--workdir`; SI and report kept outside git in `data/docs/` (owner's ok, 2026-11-18).
- Problems:
  - Reference level not validated: S7 (DLPNO-CCSD(T) clusters) not done, `06_clusters/`
    empty, basis stage E not run, while `sp_template.inp` is ready for labelling.
  - `traj_check.txt` (2026-10-24 06:21) skipped the 10 runs without `DONE`; the report of
    the same day says all 30 were checked (TODO(owner): where that check ran).
  - `runs.csv` (2026-10-13) predates the two-stage AIMD protocol (e.g. 16000 AIMD steps).
  - SI file named `SI_AlCl3urea_v0.1.pdf`; its text says draft v0.3.
  - Report: ~8-20 s per MD step; SI A.2: ~30 s on n09/n10.
  - GitHub repo first created as `alcl3-urea-` (trailing hyphen); renamed before the first
    push.
- Next: reference-level decision; SDumont runs to neumann; experiment doc for selection
  and labelling.

## 2026-11-18 — neumann — ADR-0017 carried over from hidrotopia-co2
- Goal: drop the teach-back in the template before the aimd-xgnt project starts from it.
- Done: ADR-0017 (lighter decision process) added with the number it has in
  hidrotopia-co2; ADR-0001 accepted; CLAUDE.md hard rules and task loop, experiment
  template, glossary, ADR index and the new-project ADR numbering updated (this commit).
- Results: none.
- Decisions: ADR-0017 (owner's ok, 2026-11-18); project ADRs numbered from 0101 (owner's
  ok, 2026-11-18).
- Problems: none.
- Next: `git pull template main` in aimd-xgnt before its first push.
