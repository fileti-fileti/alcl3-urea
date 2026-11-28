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

## 2026-11-28 — neumann — Third r1.0 start box (neutro) for the SDumont pilot
- Goal: answer the request of the SDumont project `alcl3-urea-mlmd` (2026-11-28): an
  r1.0 `neutro` box ([AlCl3(urea)] x 126) with the v2 recipe, shipped as PDB.
- Done:
  - `data/boxes/mlmd-v2/r1.0/neutro`: `repack_radii.py` on the v1 input with
    `radii_r1.0.json` (Packmol seed of v1), Packmol 21.2.1 (26.7 s, max violation of target
    distance 0); `build_mlmd_boxes.py check/export --ratios r1.0`.
  - Bundle `data/outbox/mlmd-boxes-r1.0-neutro-v2.tar.gz` (sha256 `6a919bab…`, full hash in
    `docs/mlmd-boxes.md`): `r1.0_neutro.pdb`, `MANIFEST.csv` (v2 columns),
    `contacts_check.txt`. Delivery note and transfer commands (neumann -> Mac -> SDumont)
    given in chat. No code change (HEAD `38e4eb4`).
  - Ledger: `cost_ledger.py add`: 0 rows; 21 jobs outside the project skipped.
- Results: neutro v1 -> v2 contacts below the AIMD r1.0 minimum 343 -> 0, smallest Cl...Cl
  2.193 -> 3.105 A; `extract_species.py` on the shipped PDB: 126 AlCl3U and nothing else,
  Al CN 4 for all; rigid molecules (RMSD <= 0.0006 A); shipped reagentes/ionico files
  unchanged (sha256 before/after). `docs/mlmd-boxes.md`.
- Decisions (owner's ok, 2026-11-28): adduct geometry from the v1 species PDB
  (`AlCl3U.pdb`, from the DTU SI `Starting_Configuration_Model_P3.xyz`, same source family
  as reagentes and ionico), not from the r10_neut GEO_OPT; bundle name
  `mlmd-boxes-r1.0-neutro-v2` (recipe version, seed name).
- Problems: none. The `alcl3-urea-mlmd` path on SDumont is inferred from ADR-0012
  (`/prj/acmes/eudes.fileti3/<repo>`), not verified.
- Next: owner carries the bundle to SDumont `data/inbox/` and checks the sha256 there;
  which steps stay here (frame selection, labels, training).

## 2026-11-24 — neumann — Clash-free r1.0 MLMD start boxes (v2); MLMD moves to SDumont
- Goal: MLMD start boxes without bad contacts; decide how many MLMD runs are needed.
- Done:
  - start-session: GitHub origin reachable (repo renamed by the owner; pushed 06:32,
    `origin/main` = `885174e`).
  - v1 diagnosis on job 4401 (`sp.out`, `init.xyz`; scratch script): the 134 atoms with
    |F| > 5 eV/A are all Cl, nearest atom of another molecule at 2.19-2.40 A (Cl 82, H 32,
    C 7, N 7, O 6); 707 heavy atoms have a heavy intermolecular neighbour < 3.0 A. Cause:
    `build_seeds.py` gives Al radius 1.8 A and every other atom 1.0 A (tolerance 2.0).
  - `932e404` `src/contacts.py` (AIMD contact reference, radii by linear program, box check);
    `cba72d4` `src/repack_radii.py`; `555c757` `--margin`; `acbf11b` `src/export_box_pdb.py`;
    `169885d` `docs/mlmd-boxes.md`.
  - Contact references: r1.0 (7 runs, 7007 frames, 16.6 min), r1.3 (7 runs), r1.5 (5 runs,
    400 K only); radii with margin 0.01 A for all three.
  - r1.0 `reagentes` and `ionico` rebuilt in `data/boxes/mlmd-v2` (Packmol 21.2.1, conda
    env `packmol`); shipped as `data/outbox/mlmd-boxes-r1.0-v2.tar.gz` (sha256 `b38c48db…`,
    full hash in `docs/mlmd-boxes.md`). Context text for the SDumont session given in chat.
  - Ledger: `cost_ledger.py add`: 0 rows; 6 jobs outside the project skipped.
- Results: v1 -> v2 contacts below the AIMD minimum 387 -> 0 (reagentes), 280 -> 0 (ionico);
  smallest Cl...Cl 2.188 -> 3.106 A and 2.198 -> 2.825 A; census unchanged; molecules rigid
  (RMSD <= 0.0006 A). `docs/mlmd-boxes.md`.
- Decisions (owner's ok, 2026-11-24):
  - No DFT GEO_OPT of the boxes; rebuild with one Packmol radius per element (P1); no DFT
    check of v2.
  - MLMD pilot (P2): r1.0 `reagentes` vs `ionico` at 400 K; in MLMD the seeds are opposite
    starts for the convergence check, not hypotheses; the pilot's time to equal speciation
    sizes the production matrix.
  - Initial test r1.0 only; r1.3/r1.5 boxes not built (references and radii ready).
  - MACE and MLMD run in another project on SDumont; this project builds the boxes and ships
    them as PDB (the machines do not connect; the owner carries them).
  - Agent's build choice: radius margin 0.01 A after the first ionico build failed by
    <= 0.0008 A; the acceptance rule was kept.
- Problems:
  - First v2 ionico build (margin 0): 11 contacts up to 0.0008 A below the AIMD minimum
    (Packmol: max violation of target distance 0.009 A).
  - `contacts.py ref` for r1.0 ran with numpy's default threads (~4.5 headnode cores); later
    runs with `OMP_NUM_THREADS=1`.
  - A Monitor waited on `pgrep -f`, which matched its own command line; stopped by hand.
  - For pairs that can bond (Al-Cl, Al-O, Al-N, N-H, O-H) the AIMD minimum sits at the
    bond-graph cutoff, so those limits are loose (the census covers accidental bonds).
  - Packmol >= 20.15 (pbc) is only in conda env `packmol`, not in `configs/machines/neumann.yaml`;
    module `packmol/20.14.3` is too old.
  - The owner declined two files (bundle README, SDumont context file); context given in chat.
- Next: owner carries the bundle to SDumont; settle which steps stay here (labels, training);
  reference-level decision.

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
