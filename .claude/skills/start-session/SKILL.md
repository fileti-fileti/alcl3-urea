---
name: start-session
description: Start a work session - read the status block and newest journal entry, check them against reality (git, Slurm queue, ended jobs, cost, purge, registered results) and give a short recap. Read-only except a fast-forward pull.
disable-model-invocation: true
---

# /start-session

Read-only: do not edit any file. Never invent a hash, job ID or number; write `unknown`.

1. Run `python3 scripts/session_facts.py --fetch` from the repo root. Its output is the
   reality to check against. `--fetch` only updates remote-tracking refs.
2. Read the `CLAUDE.md` status block, the newest entry of `docs/journal.md`, and every
   doc either of them hands off to (experiment docs, claims they name).
3. Sync (ADR-0003): if the work tree is clean and the clone is only *behind* `origin`,
   run `git pull --ff-only origin main` (explain it in one line) and say what came in
   (`git log --oneline HEAD@{1}..HEAD`). If ahead, diverged or dirty: do not pull; report
   it under Mismatches.
   On the Mac hub (remotes `neumann`/`sdumont`, no `origin`): report each remote's state;
   do not pull or push without the owner.
4. Compare: status-block claims vs git/queue/ledger facts; "last sync" lines vs
   `git log`; jobs the journal expected vs the queue and the ended jobs (give their
   error lines or report numbers from their run dirs, if readable); results whose
   checksums fail; purge rule of this machine.
5. Answer in Portuguese, at most ~25 lines, under exactly these headings:
   **Last session** · **Jobs** · **Mismatches** · **Cost** · **Now** · **Later** ·
   **Waiting on owner** · **Ask first**
   - Cost: only the ended-jobs line from the facts (since/count/units); `unknown` if
     unavailable.
   - Ask first: jobs or actions that need the owner's ok (any job, per ADR-0005).
6. Propose where to start and wait for the owner's go.
