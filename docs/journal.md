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
