# New project from lab-template

Run on the machine where the project starts (here: neumann). `<p>` is the project name
(`[a-z0-9-]+`). Paths come from `configs/machines/<machine>.yaml`
(`storage.repo_parent`, `storage.store_parent`); never guess one marked `unknown`.

## 1. Interview (guide step 1; the agent asks, max 4 questions per round)
- Research question, and what result would answer it.
- The data: where it lives on each machine (read-only legacy dirs stay in place, ADR-0008).
- Compute and budget unit per machine; ask-first limit (until set: ask before any job).
- What is confidential; language and tone (defaults: ADR-0006).
Check: the owner approves a written summary, which goes into the project's first journal
entry; the research question goes into the `CLAUDE.md` Project section.

## 2. Repos (neumann)
```bash
git clone --bare ~/git/lab-template.git ~/git/<p>.git      # project bare repo = origin, starts from the template history
git -C ~/git/<p>.git config receive.denyNonFastForwards true   # bare refuses history rewrites
git -C ~/git/<p>.git config receive.denyDeletes true           # bare refuses branch/tag deletion
git clone ~/git/<p>.git ~/<p>                               # work clone, origin = the bare repo
cd ~/<p>
git config core.hooksPath .githooks                         # turn on the pre-commit hook (per clone)
git remote add template ~/git/lab-template.git              # to bring template fixes later (ADR-0002)
```

## 3. Large storage (symlinks, ADR-0004)
```bash
mkdir -p <store_parent>/<p>-store/{data,runs,logs}
ln -s <store_parent>/<p>-store/data data
ln -s <store_parent>/<p>-store/runs runs
ln -s <store_parent>/<p>-store/logs logs
git status --porcelain --ignored | grep -E '^!! (data|runs|logs)$'   # all three ignored
```
Submit project jobs from a directory under `runs/`, so the ledger can attribute them
(ADR-0010).

## 4. Make it the project's repo
- `CLAUDE.md`: replace the Project section (research question, data locations per
  machine, legacy dirs); reset the status block (Last sync lines: this machine = today,
  others = never).
- `docs/journal.md`: first entry `## YYYY-MM-DD — <machine> — Project start` with the
  interview summary.
- Project ADRs from 0011 on (decisions of the interview that differ from the template).
- Experiments: copy `docs/experiment-template.md`.

## 5. Checks
```bash
python3 -I -m unittest discover -s tests
python3 scripts/machine_config.py detect                     # prints this machine
python3 scripts/session_facts.py                             # every section readable
```
Then commit `chore: start project <p> from lab-template` and `git push origin main`.

## 6. The other machine (through the Mac hub, ADR-0003)
One VPN at a time. On the other server, once: create `~/git/<p>.git` (bare, same two
`receive.*` settings). On the Mac:
```bash
git clone neumann:git/<p>.git ~/<p> && cd ~/<p>             # Mac clone (VPN neumann)
git remote rename origin neumann                            # name remotes after machines
git remote add sdumont sdumont:<path>/git/<p>.git           # TODO(owner): SDumont path (ADR-0004)
git push sdumont main                                       # (VPN sdumont) seed the second bare
```
On the other server: `git clone <bare> <repo_parent>/<p>`, then steps 2 (hooksPath,
template remote), 3 and 5 there.
