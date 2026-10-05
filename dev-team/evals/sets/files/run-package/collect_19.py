#!/usr/bin/env python3
"""The read-only copies run-package eval 19's harness takes after the run, in one command.

    python3 collect_19.py <copy> <outputs> <seed-sha> <root>

`<copy>` is the run's repository, `<outputs>` its `outputs/`, `<seed-sha>` the sha `seed.sh`
printed, `<root>` the plugin root the run was given (its `status.py` prints the final state).
Writes, from `<copy>`, nothing changed in it:

- `status-final.txt` — `status.py data`, run once more;
- `git-log.txt` — `git log --format='commit %H%n%B' --name-status <seed-sha>..HEAD`: every
  commit's message and the paths it added (A), modified (M) or deleted (D);
- `git-log-docs.patch` — the same commits with the patch of every path under `docs/`, so a
  commit's change to `docs/decisions.md` or to a profile can be read line by line;
- `git-status.txt` — `git status --porcelain`;
- `repo/` — the copy's `docs/`, `packages/` and `data/` (no `.git`, `.venv`, `__pycache__`);
- `stores.txt` — `find .dev-team/data -type f` with sizes, `git ls-files .dev-team`, and
  `ls -la rejects`, each under the command that printed it;
- `treatment-check.txt` — `check_treatments.py` on the copy, ending `exit: <n>`.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(args: list[str], cwd: Path) -> str:
    done = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return done.stdout + (done.stderr if done.returncode else "")


def main(copy: Path, outputs: Path, seed: str, root: Path) -> None:
    outputs.mkdir(parents=True, exist_ok=True)
    status = root / "skills/status/scripts/status.py"
    (outputs / "status-final.txt").write_text(run([sys.executable, str(status), "data"], copy))
    span = f"{seed}..HEAD"
    (outputs / "git-log.txt").write_text(run(["git", "log", "--format=commit %H%n%B", "--name-status", span], copy))
    (outputs / "git-log-docs.patch").write_text(
        run(["git", "log", "--format=commit %H%n%B", "-p", "--no-renames", span, "--", "docs/"], copy))
    (outputs / "git-status.txt").write_text(run(["git", "status", "--porcelain"], copy))
    repo = outputs / "repo"
    for part in ("docs", "packages", "data"):
        if (copy / part).exists():
            shutil.copytree(copy / part, repo / part, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
    store = copy / ".dev-team" / "data"
    listing = "\n".join(f"{p.stat().st_size:>9} {p.relative_to(copy)}" for p in sorted(store.rglob("*")) if p.is_file()) \
        if store.exists() else "no such directory"
    rejects = copy / "rejects"
    (outputs / "stores.txt").write_text(
        f"$ find .dev-team/data -type f | sort (with sizes)\n{listing or '(no file)'}\n\n"
        f"$ git ls-files .dev-team\n{run(['git', 'ls-files', '.dev-team'], copy)}\n"
        f"$ ls -la rejects\n{run(['ls', '-la', 'rejects'], copy) if rejects.exists() else 'no such directory'}\n")
    done = subprocess.run([sys.executable, str(HERE / "check_treatments.py"), str(copy),
                           "--out", str(outputs / "treatment-check.txt")], capture_output=True, text=True)
    print(f"collect_19: copies written to {outputs}; treatment check exit {done.returncode}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3], Path(sys.argv[4]).resolve())
