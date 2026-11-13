#!/usr/bin/env bash
# Block staged files that must never enter git: data/, runs/, logs/, checkpoints,
# arrays, archives, datasets (extxyz), trajectories/wavefunctions, databases,
# and any blob over MAX_BYTES. Plain .xyz (initial geometries) only hits the size limit.
# Portable: bash 3.2 (macOS) and Linux. Called by .githooks/pre-commit.
set -u
MAX_BYTES=$((1024 * 1024))   # 1 MiB, guide rule

blocked_ext='pt pth ckpt model pb h5 hdf5 npy npz pkl pickle
tar gz tgz bz2 xz zst zip 7z
wfn restart bak cube dcd xtc trr lammpstrj
extxyz traj nc db sqlite'

fail=0
while IFS= read -r -d '' f; do
  reason=""
  case "$f" in
    data|data/*|runs|runs/*|logs|logs/*) reason="lives under data/, runs/ or logs/" ;;
  esac
  if [ -z "$reason" ]; then
    base=${f##*/}
    case "$base" in
      *.*) ext=$(printf '%s' "${base##*.}" | tr '[:upper:]' '[:lower:]')
           for b in $blocked_ext; do
             [ "$ext" = "$b" ] && reason="blocked extension .$ext" && break
           done ;;
    esac
  fi
  if [ -z "$reason" ]; then
    size=$(git cat-file -s ":$f" 2>/dev/null || echo 0)
    [ "$size" -gt "$MAX_BYTES" ] && reason="staged size $size B > $MAX_BYTES B"
  fi
  if [ -n "$reason" ]; then
    echo "BLOCKED: $f ($reason)" >&2
    fail=1
  fi
done < <(git diff --cached --name-only --diff-filter=ACMR -z)

if [ "$fail" -ne 0 ]; then
  echo "Commit refused. Unstage with: git restore --staged <file>" >&2
  exit 1
fi
exit 0
