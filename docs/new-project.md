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

## 2. Repos (GitHub origin, ADR-0012)
`<user>` is the owner's GitHub account. GitHub (owner, web): new **private** repo `<p>`,
empty (no README, .gitignore or licence). Access from this machine: "GitHub access" below.
On SDumont the bootstrap kit does steps 2, 3 and 5.
```bash
git clone ~/git/lab-template.git <repo_parent>/<p>          # starts from the template history (neumann)
cd <repo_parent>/<p>
git remote rename origin template                           # template stays reachable for fixes (ADR-0002)
git remote add origin git@github-<p>:<user>/<p>.git         # GitHub is origin
git config core.hooksPath .githooks                         # turn on the pre-commit hook (per clone)
git ls-remote origin                                        # reachable; empty output = empty repo
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
  machine, legacy dirs); reset the status block (fields per ADR-0011; Now = the project's
  first tasks; Last sync lines: this machine = today, others = never).
- `docs/journal.md`: first entry `## YYYY-MM-DD — <machine> — Project start` with the
  interview summary.
- Project ADRs take the next free number (decisions of the interview that differ from
  the template).
- Experiments: copy `docs/experiment-template.md`.

## 5. Checks
```bash
python3 -I -m unittest discover -s tests
python3 scripts/machine_config.py detect                     # prints this machine
python3 scripts/session_facts.py                             # every section readable
```
Then commit `chore: start project <p> from lab-template` and `git push -u origin main`
(`-u`: the first push sets `origin/main` as upstream).

## 6. The other machine
Add a deploy key for that machine ("GitHub access"), then:
```bash
git clone git@github-<p>:<user>/<p>.git <repo_parent>/<p>   # same history as the first machine
```
Then step 2's `core.hooksPath` (and the `template` remote where lab-template is reachable),
steps 3 and 5 there.

## GitHub access (one deploy key per repo and machine, ADR-0012)
The owner types (including any passphrase):
```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_<p> -C "<p>@<machine>"   # deploy key: this repo only
```
GitHub → repo → Settings → Deploy keys → add `~/.ssh/github_<p>.pub`, tick *Allow write
access*. Then in `~/.ssh/config`:
```
Host github-<p>
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_<p>
  IdentitiesOnly yes
```
Check: `ssh -T github-<p>` (GitHub greets the repo: the key works). If port 22 is blocked:
`HostName ssh.github.com` and `Port 443`.
