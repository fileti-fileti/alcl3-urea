# CLAUDE.md — alcl3-urea

Instructions for the agent working in this repo. Personal preferences (tone, name, execution
habits) live in `~/.claude/CLAUDE.md` on each machine, not here. This file holds project
rules and conventions only. Keep it under ~160 lines; history goes to `docs/journal.md`.

## Project
- **alcl3-urea** (GitHub `fileti-fileti/alcl3-urea`, private): how does the speciation of
  AlCl3:urea electrolytes depend on the molar ratio r (1.0, 1.3, 1.5) and on temperature?
  AIMD samples configurations -> frames relabelled at a reference level -> MACE (committee,
  active learning) -> ns MLMD (LAMMPS); species by the bond graph of SI S2.2.
- Set-up: SI draft v0.3 (2026-10-14), dataset report for Davi (2026-10-24): 15 seeds (3 r x
  5 speciation hypotheses), CP2K PBE-D3(BJ)/DZVP, NVT 0.5 fs, 1 + 5 ps, 30 runs at 333-450 K.
- Claim reach: AIMD gives training frames and RDFs (per-seed local structure at 333 K only;
  reference for MLMD tests; `docs/rdf.md`). Speciation needs MLMD agreeing from opposite seeds.
- Labels: one reference level, CP2K version and input for every frame, never mixed with
  sampling energies; splits by trajectory, never by frame.
- **Confidential** (unpublished): nothing goes to an external service; structures,
  trajectories and datasets never enter git.
- People: Davi computes the labels (TODO(owner): machine, repo access).
- Data, neumann: `~/alcl3_urea_data`, legacy, **read-only** (ADR-0008): `00_inputs`,
  `01_geo`, `02_aimd/T{333,400,450}/<sys>` (20 of 30 runs complete here), `conv_test/`
  (cutoff/REL/EPS tests, `sp_template.inp`, `cp2k_data/`), `scripts/`, `cp2k_conv.py`; its
  jobs enter the ledger by `--workdir`. Frame pool onward lives in this repo (`src/`,
  `runs/`, `data/`). SI and report: `data/docs/` (TODO(owner): copy them from the Mac).
- Data, SDumont: the 10 runs made there (CP2K 2024.3) and the training/MLMD dirs
  (`datasets/vN`, `train`, `md`, `al`): TODO(owner): paths. Repo not set up there yet.

## Hard rules
- **Never fabricate** numbers, paths, versions, hyperparameters, job IDs, hashes or
  references. Unknown → `TODO(owner): <question>`, and list it in the report.
- **Fix the reading rule first** (ADR-0017). Before the output of any run that will support
  a claim or a comparison is analysed, the experiment doc fixes the method (quantity,
  analysis parameters, how the error is computed) and, for a comparison, when a difference
  counts (yes / no / inconclusive); `docs/claims.md` gets a *pending* claim with that rule.
  The rule is never changed after the results are seen; a changed rule makes a new claim.
  Benchmarks, dataset generation/labelling, tests and toy jobs are exempt (still ask-first).
- **Decisions** (ADR-0017): no teach-back. The agent proposes in 2–3 lines (what and why),
  the owner answers "ok"/"approved"; the record keeps the answer and the justification.
  ADR only for general choices on physics, protocol, analysis method or infrastructure;
  experiment-specific choices go in the experiment doc, small ones in the journal.
- **Ask first before:** submitting or cancelling **any** job (until per-machine limits are
  set, ADR-0005); deleting or overwriting files the agent did not create; force-push;
  `sudo` or any system-wide change; anything outside the repo. Existing work directories
  (`~/alcl3_urea_data`, Prussian blue, ZnCl2, ...) are **read-only**.
- **Secrets:** never ask for or write passwords, passphrases, tokens, VPN credentials or keys.
  Give the owner the command; the owner types it.
- **Explain commands:** git, SSH, VS Code and Claude Code commands get one line (what and
  why). Shell and Slurm: no explanation unless unusual.
- **Fair comparisons:** MD/AIMD: same force field or level of theory, protocol and length for
  every system compared, same analysis parameters fixed before the results are seen. MLFF:
  same model and same compute per run; validation data drawn from the training side only;
  test data never influence a choice.
- **Style:** simplest design, surgical changes, a check for every step (then run it). Show
  the diff before editing an existing file.

## Workflow
**Session loop** (one machine per session): `/start-session` (read-only recap,
fast-forward pull) → work the *Now* tasks → `/end-session` (journal, status, ledger,
results, commit, push). Skills in `.claude/skills/`; their facts come from
`python3 scripts/session_facts.py`.

**Tasks** live only in the status block (ADR-0011): *Now* (this session), *Later*
(backlog), *Waiting on owner* (blocked on the owner's decision or a fact). One line each.
A finished task leaves the block and goes to the journal entry (Done or Problems).

**Task loop** — every step has a check; run it and report its output:
1. Decision involved? Propose it in 2–3 lines; owner's "ok" before it is applied; ADR,
   experiment doc or journal as ADR-0017 says.
2. Run that will support a claim or comparison? Copy `docs/experiment-template.md`, fix
   the reading rule and add the *pending* claim before its output is analysed.
3. Job? Ask first; submit from a dir under `runs/`, clean tree, commit recorded.
4. Ended? At `/end-session`: register results, apply the fixed rule to the claim, cost
   from the ledger.

## Two machines
- `origin` is a private GitHub repo (ADR-0012): pull at `/start-session`, push at
  `/end-session`; one deploy key per (repo, machine) behind an ssh alias `github-<repo>`.
  Repos created before ADR-0012 keep their bare `origin` (`~/git/<repo>.git`) until migrated.
- Scripts detect the machine from `hostname` and read `configs/machines/<machine>.yaml`
  (strict YAML subset, unknown keys rejected; `scripts/machine_config.py detect|show|validate`).
  Paths, partitions, modules, envs and cost unit live there, never hard-coded; `unknown`
  marks an unverified fact and is never replaced by a guess.
- Scripts in `scripts/` use the Python standard library only, run on Python >= 3.6
  (neumann `/usr/bin/python3` is 3.6.8) and must not rely on the active conda env
  (neumann auto-activates `deepmd_intel` in interactive shells only).
  Job scripts activate their env explicitly, from the machine YAML.
- neumann: `/home` is NFS-exported to the nodes; `/scratch` exists on the headnode only.
- SDumont: the login node limits CPU time per process (`ulimit -t 1800`); heavy interactive
  work goes to `salloc`/`srun` on a `*_dev` partition. TODO(owner): confirm usage policy.
- CP2K: never guess MPI×threads; copy the layout of the owner's benchmarked SLURM scripts.

## Conventions
- **Journal** (`docs/journal.md`): append-only, newest first, below the marker line.
  Title: `## YYYY-MM-DD — <machine> — <short title>`; fields Goal / Done (commit hashes, job
  IDs) / Results / Decisions / Problems / Next.
- **ADRs** (`docs/decisions/NNNN-title.md`): Context → Decision (who, date) → owner's
  explanation or approval + agent's check → Consequences. Never edit an accepted ADR;
  supersede it (linked both ways). Index and template: `docs/decisions/README.md`.
- **Claims** (`docs/claims.md`): status final / provisional / pending (+ "negative").
  A number not in a claim is not stated.
- **Results** (`results/<name>/`): verbatim copies + `PROVENANCE.json`, via
  `scripts/register_result.py`; never hand-edited. Legacy results enter as `legacy-*`
  (ADR-0008).
- **Cost**: one ledger per machine, `results/cost_ledger_<machine>.csv`, appended by
  `scripts/cost_ledger.py` from scheduler accounting; failed and cancelled jobs count.
  Only jobs submitted under `runs/` (or given with `--jobs`) are charged to the project
  (ADR-0005, ADR-0009, ADR-0010).
- **Runs** record the exact commit (`git rev-parse HEAD`) and refuse a dirty tree.
- **Never in git**: `data/`, `runs/`, `logs/` (gitignored; symlinks to large storage),
  extensions in `scripts/blocked_extensions.txt` (checkpoints, arrays, archives,
  datasets, trajectories), files > 1 MiB. Enforced by `.githooks/pre-commit` →
  `scripts/check_staged_files.sh`.
- Docs in English; chat with the owner in Portuguese (ADR-0006).
- Commit messages: `<type>: <summary>` (feat, fix, docs, chore, test).

## Where things live
| Question | Place |
|---|---|
| What is true now? | status block below |
| What do we do next? | status block: Now / Later / Waiting on owner |
| What happened? | `docs/journal.md` |
| Why is it built this way? | `docs/decisions/` |
| What can we state? | `docs/claims.md` |
| What is it based on? | `results/<name>/` |
| What did it cost? | `results/cost_ledger_<machine>.csv` |
| What does this word mean? | `docs/glossary.md` |
| Who said so? | `docs/references.bib` (entry only after a Crossref/arXiv check) |
| Machine facts | `configs/machines/<machine>.yaml` |
| Python envs (record only) | `envs/<machine>.environment.yml` |
| Agent permissions | `.claude/settings.json` (ask: jobs, push; deny: force-push, `rm -rf`, edits in `results/`) |

## New clone checklist
1. `git config core.hooksPath .githooks` (turns on the pre-commit hook; per clone).
2. Create the `data`, `runs`, `logs` symlinks to the machine's storage (project repos only).
3. Run the tests: `python3 -I -m unittest discover -s tests` (stdlib only).
4. `scripts/machine_config.py detect` prints this machine's name (else add/fix its YAML).

## Status
<!-- BEGIN STATUS -->
- Updated: 2026-11-18 — neumann
- State: started from lab-template `24e4016` (ADRs 0001-0012, 0017). Legacy dir: GEO_OPT and
  30 AIMD runs ended (20 complete on neumann, 10 on SDumont); convergence stages A, B, D
  ended 2026-10-26 (jobs 4250-4261), `sp_template.inp` written; no frame selected or
  labelled. Not set up on SDumont.
- Now:
  - Reference level: keep PBE-D3(BJ)/DZVP or run S7 / basis stage E first (before labelling).
  - Bring the 10 SDumont runs to the neumann store and check them before frame selection.
  - Experiment doc for frame selection and labelling (quotas, splits, QC) before any pick.
- Later:
  - Copy the pipeline scripts from the legacy dir into `src/`.
  - SI v0.4: Table S7 census; CP2K 2024.1 vs 2024.3 energy check; MAX_SCF 50x20 check;
    r = 1.3 density (Liu 2017); production QC of the 30 runs (SI S6.3).
  - SDumont: deploy key, clone, LNCC paths, ledger of the SDumont jobs.
  - SI references into `docs/references.bib` after a Crossref check.
- Waiting on owner: Davi (machine, repo access); where the 10 SDumont runs and the 30-run
  package for Davi live now; LNCC paths; SI and report copies (and editable sources).
- Last sync — neumann: 2026-11-18, pushed to origin on top of `24e4016`
- Last sync — sdumont: never (not cloned)
<!-- END STATUS -->
