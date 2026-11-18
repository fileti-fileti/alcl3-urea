# <experiment name>

Copy to `docs/<experiment>.md`. Fill Question, Design and Reading rule, and add the
*pending* claim to `docs/claims.md`, before the output of any run that will support a claim
or a comparison is analysed (CLAUDE.md, Hard rules; ADR-0017).

## Question
## Design
- Data (paths via `data/`), model, hyperparameters (from configs, never from memory)
- Fair comparison: same model and same compute per run; validation from the training
  side only; test data never influence a choice
## Reading rule (fixed before the result; date)
- Method: quantity, analysis parameters, how the error is computed
- Comparison only: when a difference counts (yes / no / inconclusive)
- Claim: `docs/claims.md` ID-n (pending)
## How to run
- Commit (`git rev-parse HEAD`, clean tree), machine, partition, job script, run dir
  under `runs/`
## Results
- Registered in `results/<name>/`; table printed by: <command>
- Jobs: IDs. Cost: `scripts/cost_ledger.py sum --jobs ...`
