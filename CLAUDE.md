# CLAUDE.md — lab-template

Instructions for the agent working in this repo. Personal preferences (tone, name, execution
habits) live in `~/.claude/CLAUDE.md` on each machine, not here. This file holds project
rules and conventions only. Keep it under ~160 lines; history goes to `docs/journal.md`.

## Project
- `lab-template` is the template for MLFF research repos (MACE/DeePMD, CP2K, LAMMPS, GROMACS)
  across two machines: **neumann** (UNIFESP, own cluster) and **sdumont** (LNCC).
- Projects are created from it (`docs/new-project.md`, TODO: written in a later block); each
  project replaces this section with its research question and data locations.
- Experiment parts (`docs/<experiment>.md`, `docs/claims.md`) exist here as skeletons only
  (ADR-0001).

## Hard rules
- **Never fabricate** numbers, paths, versions, hyperparameters, job IDs, hashes or
  references. Unknown → `TODO(owner): <question>`, and list it in the report.
- **Fix the reading rule first.** Before any run whose result will support a claim or a
  comparison, the experiment doc states the question, the metric, the threshold and what
  counts as yes or no, and `docs/claims.md` gets a *pending* claim with that rule. The rule
  is never changed after the results are seen; a changed rule makes a new claim.
  Benchmarks, dataset generation/labelling, tests and toy jobs are exempt (still ask-first).
- **Teach-back** for research/methodology decisions (reading rules, claims, comparisons,
  metrics): a proposal until the owner explains it in their own words and the agent checks
  it is right and complete (say exactly what is missing). Paste the owner's words in the ADR.
- **Infrastructure decisions** (layout, sync, ledger, naming, tooling): the agent explains
  in ~2 lines, the owner answers "approved"; the ADR records the approval and the agent's
  justification (ADR-0001).
- **Ask first before:** submitting or cancelling **any** job (until per-machine limits are
  set, ADR-0005); deleting or overwriting files the agent did not create; force-push;
  `sudo` or any system-wide change; anything outside the repo. Existing work directories
  (Prussian blue, ZnCl2, AlCl3, ...) are **read-only**.
- **Secrets:** never ask for or write passwords, passphrases, tokens, VPN credentials or keys.
  Give the owner the command; the owner types it.
- **Explain commands:** git, SSH, VS Code and Claude Code commands get one line (what and
  why). Shell and Slurm: no explanation unless unusual.
- **Fair comparisons:** same model and same compute per run; validation data drawn from the
  training side only; test data never influence a choice.
- **Style:** simplest design, surgical changes, a check for every step (then run it). Show
  the diff before editing an existing file.

## Two machines
- VPNs are mutually exclusive: one machine at a time. Sync goes through the Mac (ADR-0003):
  each server has a bare repo (`~/git/<repo>.git`, `origin`) plus a work clone; the Mac clone
  has remotes `neumann` and `sdumont`. Pull at `/start-session`, push at `/end-session`.
- Scripts detect the machine from `hostname` and read `configs/machines/<machine>.yaml`
  (validated; unknown keys rejected). Paths, partitions, modules, envs and cost unit live
  there, never hard-coded.
- Scripts in `scripts/` use the Python standard library only and must not rely on the
  active conda env (neumann auto-activates `deepmd_intel` in interactive shells only).
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
  `scripts/cost_ledger.py` from scheduler accounting; failed and cancelled jobs count
  (ADR-0005, ADR-0009).
- **Runs** record the exact commit (`git rev-parse HEAD`) and refuse a dirty tree.
- **Never in git**: `data/`, `runs/`, `logs/` (gitignored; symlinks to large storage),
  checkpoints, arrays, archives, datasets, trajectories, files > 1 MiB. Enforced by
  `.githooks/pre-commit` → `scripts/check_staged_files.sh`.
- Docs in English; chat with the owner in Portuguese (ADR-0006).
- Commit messages: `<type>: <summary>` (feat, fix, docs, chore, test).

## Where things live
| Question | Place |
|---|---|
| What is true now? | status block below |
| What happened? | `docs/journal.md` |
| Why is it built this way? | `docs/decisions/` |
| What can we state? | `docs/claims.md` |
| What is it based on? | `results/<name>/` |
| What did it cost? | `results/cost_ledger_<machine>.csv` |
| What does this word mean? | `docs/glossary.md` |
| Who said so? | `docs/references.bib` (entry only after a Crossref/arXiv check) |
| Machine facts | `configs/machines/<machine>.yaml` |

## New clone checklist
1. `git config core.hooksPath .githooks` (turns on the pre-commit hook; per clone).
2. Create the `data`, `runs`, `logs` symlinks to the machine's storage (project repos only).
3. Run the tests: TODO: command fixed when the scripts exist (setup F5, block 3).

## Status
<!-- BEGIN STATUS -->
- Updated: 2026-11-13 — neumann
- Phase: template under construction (setup F5). Done: layout, .gitignore, pre-commit hook,
  CLAUDE.md, docs skeleton, ADRs 0001-0009 (0001 Proposed). Next: scripts with tests,
  machine YAMLs, settings, skills.
- Last sync — neumann: `02e5187` 2026-11-13 (bare = work clone)
- Last sync — sdumont: never (not cloned)
- Last sync — mac: never (not cloned)
- Waiting on owner: teach-back on the research rules of ADR-0001; SDumont parts of
  ADR-0004/0005 (TODO(owner)).
<!-- END STATUS -->
