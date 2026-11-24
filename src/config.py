"""
config.py — single source of parameters for the AlCl3:urea dataset factory (neumann).
Edit here, then re-run:  python scripts/make_inputs.py
"""

# ----------------------------------------------------------------------------- CP2K
CP2K = {
    "cutoff": 400,               # Ry  (sampling level; REFTRAJ relabel uses a higher cutoff later)
    "rel_cutoff": 50,            # Ry
    "basis": "DZVP-MOLOPT-SR-GTH",
    "potentials": {"H": "GTH-PBE-q1", "C": "GTH-PBE-q4", "N": "GTH-PBE-q5",
                   "O": "GTH-PBE-q6", "Al": "GTH-PBE-q3", "Cl": "GTH-PBE-q7"},
    "functional": "PBE",
    "d3": "DFTD3(BJ)",           # or "DFTD3" (zero damping, as in the ZnCl2 project)
    "d3_cutoff": 15.0,           # angstrom
    "eps_scf": 1.0e-6,
}

# ------------------------------------------------------------------------- GEO_OPT
GEO = {
    "optimizer": "LBFGS",
    "max_iter": 300,
    "max_force": 1.0e-3,         # Ha/bohr (~0.05 eV/A): loose on purpose, only removes packing clashes
    "rms_force": 5.0e-4,
}

# ---------------------------------------------------------------------------- AIMD
# Each run starts from the last GEO_OPT frame (+ its wavefunction).
# 'seeds' selects systems by seed suffix (r15_ionA -> 'ionA'); "all" = every system.
AIMD = {
    "timestep": 0.5,             # fs
    "thermostat": "CSVR",
    "timecon": 100,              # fs
    "print_every": 10,           # steps -> one frame every 5 fs
    "restart_every": 200,        # steps
    "discard_ps": 1.0,           # equilibration skipped later by extract_frames.py (not used here)
    "runs": {
        "T400": {"T": 400, "ps": 8.0, "seeds": "all"},
        "T333": {"T": 333, "ps": 6.0, "seeds": ["ion", "ionA", "ionB", "mist"]},
        "T450": {"T": 450, "ps": 6.0, "seeds": ["reag", "neut", "fora"]},
    },
}

# --------------------------------------------------------------------------- SLURM
# Each system (its GEO_OPT + all its AIMD runs) is pinned to one node with --nodelist.
# A node with slots > 1 runs that many jobs side by side (n12: 4 x 112 cores).
# Systems are spread over the slots automatically (greedy, cost ~ natoms^2 * ps / cores);
# to force a placement, add it to "assign", e.g. {"r13_reag": "n11"}.
SLURM = {
    "header": [
        "#SBATCH --partition=batch",
        "#SBATCH --nodes=1",
    ],
    "nodes": {                    # node: (cores per job, jobs side by side)
        "n09": (128, 1),
        "n10": (128, 1),
        "n11": (96, 1),
        "n12": (112, 4),
    },
    "assign": {},
    "time_geo": "2-00:00:00",
    "time_md": "7-00:00:00",
    "cp2k_walltime_margin_min": 30,   # CP2K stops cleanly this many minutes before the Slurm limit
    "module": "cp2k/2024.1-gcc-12.2.0-iy4ur5k",
    "mpirun": "mpirun --mca opal_set_max_sys_limits 1 --mca btl ^openib",
    "exe": "cp2k.psmp",
}
