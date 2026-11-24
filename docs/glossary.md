# Glossary

One line per term.

- **ADR**: Architecture Decision Record, `docs/decisions/NNNN-*.md`; never edited once accepted, only superseded.
- **Bare repo**: a git repo with no working tree; `origin` of the neumann repos created before ADR-0012.
- **Claim**: a statement in `docs/claims.md` with a reading rule fixed before the result.
- **Contact reference**: smallest intermolecular distance per element pair over AIMD frames of one composition (`src/contacts.py ref`); sets the Packmol radii and the box check (`docs/mlmd-boxes.md`).
- **Deploy key**: an ssh key with access to one GitHub repo only; one per (repo, machine) (ADR-0012).
- **Ledger**: `results/cost_ledger_<machine>.csv`, one row per ended job.
- **MLMD box**: ~1500-atom cubic Packmol box for MLMD, `data/boxes/mlmd-v2/<r>/<seed>/` (v1 has Cl...Cl clashes, do not use); not equilibrated.
- **Opposite starts**: two MLMD runs of one state point from seeds of opposite speciation (e.g. `reagentes`, `ionico`); equilibrium when both reach the same speciation.
- **Reading rule**: method (quantity, analysis parameters, error) and, for a comparison, when
  a difference counts (yes/no/inconclusive), fixed before the output is analysed (ADR-0017).
- **Registered result**: verbatim copy under `results/<name>/` with `PROVENANCE.json` checksums.
- **SP test**: CP2K single point (ENERGY_FORCE) of an MLMD box at the AIMD level, to see how clashed it is (`runs/sp-boxes-v1`).
- **Status block**: the part of `CLAUDE.md` between the STATUS markers; current state only.
- **Teach-back**: the owner explains a research decision in their own words before it is
  adopted. Dropped by ADR-0017.
