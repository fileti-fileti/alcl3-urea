# Glossary

One line per term.

- **ADR**: Architecture Decision Record, `docs/decisions/NNNN-*.md`; never edited once accepted, only superseded.
- **Bare repo**: a git repo with no working tree; `origin` of the neumann repos created before ADR-0012.
- **Claim**: a statement in `docs/claims.md` with a reading rule fixed before the result.
- **Deploy key**: an ssh key with access to one GitHub repo only; one per (repo, machine) (ADR-0012).
- **Ledger**: `results/cost_ledger_<machine>.csv`, one row per ended job.
- **Reading rule**: question, metric, threshold and what counts as yes/no, fixed before a run.
- **Registered result**: verbatim copy under `results/<name>/` with `PROVENANCE.json` checksums.
- **Status block**: the part of `CLAUDE.md` between the STATUS markers; current state only.
- **Teach-back**: the owner explains a research decision in their own words before it is adopted.
