# MLMD start boxes (mlmd-v2)

## Scope (owner, 2026-11-24)
- MACE training and MLMD run in another project on SDumont (GPUs). neumann and SDumont do
  not connect: this project builds the start boxes, checks them and ships them as PDB; the
  owner carries them over, where they are converted and enter the MLMD protocol.
- Initial test: r = 1.0 only, seeds `reagentes` (reactants, molecular) and `ionico` (fully
  ionic). They are opposite starts: equilibrium is judged by both runs reaching the same
  speciation (pilot, P2). r = 1.3 and 1.5: contact references and radii computed, boxes
  not built.

## Problem with v1 (`data/boxes/mlmd-v1`, built 2026-11-21)
- Packmol radii in `build_seeds.py`: Al 1.8 A, every other atom tolerance/2 = 1.0 A, so any
  intermolecular pair could sit at 2.0 A, Cl...Cl included.
- Single point, job 4401 (r1.0/neutro): all 134 atoms with |F| > 5 eV/A are Cl; their
  nearest atom of another molecule is at 2.19-2.40 A (Cl 82, H 32, C 7, N 7, O 6);
  |F| max 9.64 eV/A.
- Not done: DFT GEO_OPT of the boxes (estimated order 10^3 core-hours per box, a 0 K minimum
  at the sampling level, risk of artificial Al-Cl-Al bridges from the clashes); DFT check of
  the v2 boxes (owner: not needed).

## Recipe (v2)
1. **Contact reference** (`src/contacts.py ref`): every AIMD run of the same composition at
   333 and 400 K complete on neumann; production steps 0-10000 every 10. Molecules are the
   components of the `extract_species.find_bonds` graph (the census criterion); per element
   pair, dmin = smallest intermolecular distance over all frames.
   - r1.0: T333 r10_ion, r10_mist; T400 r10_fora, r10_ion, r10_mist, r10_neut, r10_reag.
   - r1.3: T333 r13_ionA, r13_mist; T400 r13_ionA, r13_ionB, r13_mist, r13_neut, r13_reag.
   - r1.5: T400 r15_ionA, r15_ionB, r15_mist, r15_neut, r15_reag (none complete at 333 K
     on neumann).
   - For pairs that can bond (Al-Cl, Al-O, Al-N, N-H, O-H) dmin sits at the bond-graph
     cutoff (bonds fluctuating across it), so their limit is loose; the species census
     catches accidental bonds.
2. **Radii** (`src/contacts.py radii --margin 0.01`): one Packmol radius per element, the
   smallest contact-weighted set with R_a + R_b >= dmin_ab (linear program), plus 0.01 A
   per radius (Packmol meets target distances to ~0.01 A).

   | Radius (A) | Al | C | Cl | H | N | O |
   |---|---|---|---|---|---|---|
   | r1.0 | 1.748 | 1.465 | 1.413 | 0.794 | 1.279 | 1.141 |
   | r1.3 | 1.763 | 1.484 | 1.414 | 0.758 | 1.295 | 1.160 |
   | r1.5 | 1.713 | 1.461 | 1.368 | 0.847 | 1.328 | 1.230 |
3. **Repack** (`src/repack_radii.py`): the v1 `packmol.inp` with the new radii; same
   structures, counts, ion anchors, Packmol seed and box. Packmol 21.2.1 (conda env
   `packmol`), as for v1.
4. **Census and export**: `src/build_mlmd_boxes.py check` and `export` (same tests as v1),
   then `src/export_box_pdb.py` (PDB for transfer).

## Acceptance (fixed before the boxes were built)
- Species census equal to the target (ratio exact, charge 0).
- No intermolecular contact below the AIMD dmin of its element pair (`contacts.py box`),
  run on the PDB files that are shipped.
- PDB read back equal to `packed.xyz` (element order, positions modulo L).
- Also checked once (scratch script): molecules rigid (RMSD to the species PDB), `start.data`
  equal to `packed.xyz` with types 1 Al 2 C 3 Cl 4 H 5 N 6 O, atoms inside [0, L).

## Results (r1.0, 2026-11-24)
| Check | reagentes v1 -> v2 | ionico v1 -> v2 |
|---|---|---|
| Contacts below the AIMD dmin | 387 -> 0 | 280 -> 0 |
| Smallest Cl...Cl (AIMD dmin 2.805 A) | 2.188 -> 3.106 A | 2.198 -> 2.825 A |
| Census | Al2Cl6 63, urea 126 | AlCl2U2_p 63, AlCl4_m 63 |
| Max RMSD to species PDB | 0.0006 A | 0.0006 A |

- Both: 1512 atoms, L = 29.729979 A, rho = 1.5398 g/cm3 (as v1). Not equilibrated.
- First v2 build without margin: ionico had 11 contacts up to 0.0008 A below dmin (FAIL).
  The acceptance rule was kept; the margin was added and both boxes rebuilt.

## Files
- `data/boxes/mlmd-v2/`: `contacts_ref_r{1.0,1.3,1.5}.json` (r1.3/r1.5 with `.log`),
  `radii_r{1.0,1.3,1.5}.json`, `manifest.csv`, `r1.0/{reagentes,ionico}/` (`packmol.inp`,
  `packmol.log`, `packed.pdb`, `packed.xyz`, `start.data`, species PDBs).
- Transfer bundle: `data/outbox/mlmd-boxes-r1.0-v2/` (2 PDB, `MANIFEST.csv` with sha256,
  `contacts_check.txt`) and `mlmd-boxes-r1.0-v2.tar.gz`
  (sha256 `b38c48db8427cfcbfaaed429b958b43e61ce87fe4891bbfbf656778e1fb2cba7`).
- Scripts: `src/contacts.py` (`932e404`, `555c757`), `src/repack_radii.py` (`cba72d4`),
  `src/export_box_pdb.py` (`acbf11b`).

## How to run (r1.0)
Interactive on the headnode; set `OMP_NUM_THREADS=1` (the reference for r1.0 took 16.6 min
and ~4.5 cores with numpy's default threads). `PY` = deepmd_intel python, called with `-I`.
```
$PY src/contacts.py ref <7 run dirs> -o data/boxes/mlmd-v2/contacts_ref_r1.0.json
$PY src/contacts.py radii data/boxes/mlmd-v2/contacts_ref_r1.0.json --margin 0.01 \
    -o data/boxes/mlmd-v2/radii_r1.0.json
python3 src/repack_radii.py data/boxes/mlmd-v1/r1.0/<seed> data/boxes/mlmd-v2/r1.0/<seed> \
    --radii data/boxes/mlmd-v2/radii_r1.0.json
(cd data/boxes/mlmd-v2/r1.0/<seed> && ~/miniforge3/envs/packmol/bin/packmol < packmol.inp > packmol.log)
$PY src/build_mlmd_boxes.py check  -o data/boxes/mlmd-v2 --ratios r1.0
$PY src/build_mlmd_boxes.py export -o data/boxes/mlmd-v2 --ratios r1.0
python3 src/export_box_pdb.py data/boxes/mlmd-v2/r1.0/<seed> -o <bundle>/r1.0_<seed>.pdb
$PY src/contacts.py box data/boxes/mlmd-v2/contacts_ref_r1.0.json <bundle>/*.pdb
```
