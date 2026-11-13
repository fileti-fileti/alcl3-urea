# CLAUDE.md — lab-template

Instructions for the agent working in this repo. Personal preferences (tone, name, execution
habits) live in `~/.claude/CLAUDE.md` on each machine, not here. This file holds project
rules and conventions only. Keep it under ~160 lines; history goes to `docs/journal.md`.

## Project
- `lab-template` is the template for MLFF research repos (MACE/DeePMD, CP2K, LAMMPS, GROMACS)
  across two machines: **neumann** (UNIFESP, own cluster) and **sdumont** (LNCC).
- Projects are created from it by `docs/new-project.md`; each project replaces this
  section with its research question and data locations.
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

## Workflow
**Session loop** (one machine per session): `/start-session` (read-only recap,
fast-forward pull) → work the *Now* tasks → `/end-session` (journal, status, ledger,
results, commit, push). Skills in `.claude/skills/`; their facts come from
`python3 scripts/session_facts.py`.

**Tasks** live only in the status block (ADR-0011): *Now* (this session), *Later*
(backlog), *Waiting on owner* (blocked on the owner's decision or a fact). One line each.
A finished task leaves the block and goes to the journal entry (Done or Problems).

**Task loop** — every step has a check; run it and report its output:
1. Decision involved? Research/methodology → teach-back; infrastructure → owner's
   "approved". Either way an ADR before it is applied.
2. Run that will support a claim or comparison? Copy `docs/experiment-template.md`, fix
   the reading rule and add the *pending* claim before anything runs.
3. Job? Ask first; submit from a dir under `runs/`, clean tree, commit recorded.
4. Ended? At `/end-session`: register results, apply the fixed rule to the claim, cost
   from the ledger.

## Two machines
- VPNs are mutually exclusive: one machine at a time. Sync goes through the Mac (ADR-0003):
  each server has a bare repo (`~/git/<repo>.git`, `origin`) plus a work clone; the Mac clone
  has remotes `neumann` and `sdumont`. Pull at `/start-session`, push at `/end-session`.
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
- Updated: 2026-11-13 — neumann
- State: template skeleton on neumann (layout, hook, scripts with tests, machine YAMLs,
  repo settings, skills, docs, ADRs 0001-0011; 0001 Proposed). Not set up on SDumont.
- Now:
  - Teach-back on the research rules of ADR-0001 (blocks any experiment doc or claim).
  - Check the session loop: `/end-session` → new session → `/start-session` (guide step 5).
- Later:
  - SDumont: setup F3/F4, bare repo + clone, ledger merge check.
  - Toy job on neumann to exercise `cost_ledger.py add` on a real job (needs the owner's ok).
  - Bring template changes into `~/sandbox` through its `template` remote (ADR-0002 path).
  - Env records for the Mac and SDumont (ADR-0007).
- Waiting on owner: SDumont facts for ADR-0004/0005 (TODO(owner)).
- Last sync — neumann: 2026-11-13, pushed to origin on top of `ac82332`
- Last sync — sdumont: never (not cloned)
- Last sync — mac: never (not cloned)
<!-- END STATUS -->
