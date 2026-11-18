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
