# AIMD RDFs (rdf-aimd-v1)

Method fixed 2026-11-18, before any RDF was computed (ADR-0017). Owner's ok: "ok pra tudo"
(2026-11-18) to the pairs, parameters, names, comparison rule with k = 2, and the claim
reach below.

## Question
1. Local structure of each speciation hypothesis (seed) at 333 K, from PBE-D3(BJ)/DZVP
   AIMD: distances and coordination numbers of Al–Cl (terminal, bridging), Al–O (urea),
   Al–Al (dimers) and of the hydrogen-bond network (N–H···Cl, N–H···O).
2. Reference for MLMD tests: does a MACE model reproduce the AIMD RDFs of a run it was not
   trained on?

## Design
- Data: production of the AIMD runs in `~/alcl3_urea_data/02_aimd/T<T>/<system>/` (legacy,
  read-only, ADR-0008). On neumann, 20 of 30 runs are complete; the 10 SDumont runs are
  added to `rdf-aimd-v1` when they reach neumann, with the same script version.
- Reach: speciation does not equilibrate in 6 ps, so every run keeps its seed (SI S3.2).
  RDFs describe each seed, never the equilibrium liquid; no average over seeds. Runs at
  400 and 450 K are at the 333-K density (elevated pressure, SI S6.1): references for MLMD
  tests only, not structural characterisation.
- MLMD test, fair comparison: the MLMD run repeats the AIMD run (same `init.xyz`, N, L, T,
  0.5 fs, CSVR massive 10 fs for 1 ps then global 100 fs for 5 ps, frames every 5 fs) and
  is analysed by the same `src/rdf.py` version. The model's labels are at the AIMD level
  (PBE-D3(BJ)/DZVP-MOLOPT-SR-GTH, GTH-PBE); the run was held out of training (split by
  trajectory). If the model was tuned against these RDFs they are validation, and the test
  needs other held-out runs.

## Reading rule (fixed 2026-11-18, before the result)
- Pairs: Al–Cl, Al–O, Al–N, Al–Al, Cl–Cl, Cl–H, O–H, C–O, C–N, N–H.

  | Pair | Role |
  |---|---|
  | Al–Cl | terminal vs bridging Cl (AlCl4-, Al2Cl7-, Al2Cl6); Al chloride coordination |
  | Al–O | urea bound to Al through O (adducts, cations) |
  | Al–N | checks O- vs N-binding; second shell of bound urea |
  | Al–Al | dimers (Al2Cl7-, Al2Cl6, [Al2Cl5U2]+) vs separate Al centres |
  | Cl–Cl | AlCl4 tetrahedra and anion packing |
  | Cl–H | N–H···Cl hydrogen bonds (anion–urea) |
  | O–H | N–H···O hydrogen bonds (urea–urea) |
  | C–O, C–N, N–H | internal geometry of urea (model check) |
- Frames: production steps 0–10000 every 10 (1001 frames, 5 ps); equilibration excluded.
  Steps written twice by restarts: the last written copy is kept. A run without exactly
  these steps is not used.
- g_ab(r): all pairs (intra + intermolecular), minimum image in the cubic box of
  `prod.inp`, r ≤ 9.70 Å (below L/2 of the smallest box), bins of 0.02 Å.
  n_ab(r): running count of b atoms per a atom up to the bin's upper edge.
- Error: 5 blocks of consecutive frames (~1 ps each); SE = SD of the block values / √5.
- Derived quantities (claims), on the 0.02-Å curve, the same for AIMD and MLMD:
  - r1: first local maximum with g ≥ 1 that is also the highest point within ±0.2 Å;
    height g(r1).
  - rmin: first local minimum after r1 that is the lowest point within ±0.2 Å;
    CN = n(rmin).
  - SE of each from the same definitions applied to each block; SE of a position is at
    least 0.02/√12 Å (bin quantisation).
- Comparison (MLMD vs AIMD, same system and T): for each pair, r1, g(r1) and CN at the
  AIMD rmin. A difference counts if |Δ| > 2 √(SE_AIMD² + SE_MLMD²): **differs**; else
  **agrees**; **inconclusive** if the MLMD run does not meet the Design conditions. With
  30 tests per run, about 1–2 "differs" are expected by chance at k = 2: each difference is
  reported, not reduced to one pass/fail.
- Claims: RDF-1, RDF-2 in `docs/claims.md` (pending).

## How to run
- Interactive on the headnode (analysis, not a job). Clean `src/`, commit recorded in each
  `.json`. Interpreter: `/home/eudes/miniforge3/envs/analysis/bin/python -I` (numpy).
- `src/rdf.py selftest`, then per run:
  `src/rdf.py aimd <run_dir> --name <system>.T<T>.aimd -o runs/rdf-aimd-v1`
- MLMD later: `src/rdf.py xyz <traj.xyz> --box <L> --name <system>.T<T>.mlmd-<model> -o <dir>`
  (element symbols in the xyz; `i = <step>` in the comment line if steps repeat).

## Files
- One CSV per run: `<system>.T<T>.<source>.rdf.csv`, source = `aimd` or `mlmd-<model>`.
  Columns: `r_center_A`, `r_upper_A`, then `g_<pair>`, `se_<pair>`, `cn_<pair>` per pair.
- `<system>.T<T>.<source>.rdf.json`: parameters, frames, box, atom counts, sha256 of every
  source trajectory file, repo commit, script sha256.

## Results
- Registered in `results/rdf-aimd-v1/` (2026-11-18, `src/rdf.py` at `3115ddd`): 20 runs,
  1001 frames each. Missing: the 10 SDumont runs (T333 r13_ionB, r15_ionA, r15_ionB,
  r15_mist; T450 r10_fora, r10_neut, r10_reag, r13_neut, r15_neut, r15_reag).
- QC: finite values, 10 pairs per file, non-decreasing n(r); tails (r > 8 Å) of the pairs
  with few atoms (Al–Al, C–O, C–N, O–H) are noisier than those of Al–Cl and Cl–H.
- RDF-1 and RDF-2 not yet evaluated.
