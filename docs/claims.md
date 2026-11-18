# Claims

A number that is not here is not stated. Status: final, provisional or pending; add
"negative" when the result went against the hypothesis. The rule is fixed before the
result and never changed afterwards; a changed rule makes a new claim.

```
### ID-1. <the claim, as a question or a statement> (status)
- Rule, fixed before the result: ...
- Numbers: copied from the registered files or from a report script run on them, never from memory
- Reading: what the rule says the numbers mean
- Limits: seeds, sizes, what was not tested
- Evidence: results/<name>/ and the command that prints the table
- Method: link to the doc section. Jobs: IDs. Cost: from the ledger
```

### RDF-1. Local structure of each seed at 333 K from AIMD, PBE-D3(BJ)/DZVP (pending)
- Rule, fixed before the result: `docs/rdf.md` (Reading rule): r1, g(r1) and CN at rmin
  ± block SE, per pair and per seed; descriptive only.
- Limits: per seed, never the equilibrium liquid (seed memory, 5 ps); 333 K only; 4 of the
  8 runs at 333 K are on neumann (r10_ion, r10_mist, r13_ionA, r13_mist).
- Evidence: `results/rdf-aimd-v1/`.

### RDF-2. A MACE model reproduces the AIMD RDFs of runs held out of its training (pending)
- Rule, fixed before the result: `docs/rdf.md` (Comparison): per pair, r1, g(r1) and CN at
  the AIMD rmin; differs if |Δ| > 2 × combined SE, else agrees; inconclusive if the MLMD
  run does not repeat the AIMD run or the run was in the training set.
- Evidence: `results/rdf-aimd-v1/` and the MLMD RDFs (not yet run).
