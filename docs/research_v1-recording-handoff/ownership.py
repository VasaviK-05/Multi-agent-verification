"""Compare committed, staged, unstaged and untracked paths to a pinned base."""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def unexpected_changes(paths, manifest):
    return sorted(p for p in paths if p not in manifest['allowed_files']
                  and not any(p.startswith(prefix) for prefix in manifest['allowed_prefixes']))


def changed_paths(repo, base):
    # Exclude upstream-only changes when the feature is behind reviewed main.
    # Still include all feature commits, staging, worktree and untracked paths.
    merge_base = subprocess.check_output(['git', 'merge-base', 'HEAD', base], cwd=repo).decode('ascii').strip()
    tracked = subprocess.check_output(['git', 'diff', '--name-only', '-z', merge_base, '--'], cwd=repo)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=repo)
    return sorted(set(p.decode('utf-8') for p in (tracked + untracked).split(b'\0') if p))


def check(repo=REPO):
    manifest = json.loads((HERE/'owned-files.json').read_text())
    paths = changed_paths(repo, manifest['base_commit'])
    bad = unexpected_changes(paths, manifest)
    if bad:
        raise ValueError('Unexpected files outside game-owned scope: ' + ', '.join(bad))
    return paths


if __name__ == '__main__':
    print(json.dumps({'unexpected': [], 'changed_files': check()}, indent=2))
