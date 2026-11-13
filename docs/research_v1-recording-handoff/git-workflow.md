# Authorized feature-branch workflow — commands only, not executed

Current branch is uncommitted and based on 4c2a2eb. Reviewed remote main was 3e8769075420b4bf3e565bf46854f55a77a4a35f; its only newer changes are the migration runner/tests, with no game-side path overlap. The proposed patch applies cleanly there. Do not mistake a two-dot diff's missing upstream migration changes for intentional teammate edits.

Run the following **only after explicit authorization to commit**. Use the isolated checkout, not the shared Experiment 1 checkout. The existing origin is local and must not receive a push. Inspect any preexisting `github-review` remote rather than replacing it blindly.

```sh
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
git branch --show-current
git status --short
git remote -v
# Add once, if this remote name is absent:
git remote add github-review https://github.com/VasaviK-05/Multi-agent-verification.git
git fetch --no-tags github-review main
test "$(git rev-parse github-review/main)" = 3e8769075420b4bf3e565bf46854f55a77a4a35f
# If the equality fails, stop and repeat latest-main review before continuing.

# Stage exactly the reviewed public allowlist, never the whole directory:
python3 - <<'PY'
import json, subprocess
from pathlib import Path
m=json.loads(Path('docs/research_v1-recording-handoff/public-commit-files.json').read_text())
subprocess.run(['git','add','--',*m['files']],check=True)
PY

git diff --cached --check
python3 - <<'PY'
import json, subprocess
from pathlib import Path
expected=set(json.loads(Path('docs/research_v1-recording-handoff/public-commit-files.json').read_text())['files'])
actual=set(p.decode() for p in subprocess.check_output(['git','diff','--cached','--name-only','-z']).split(b'\0') if p)
assert actual==expected, {'unexpected':sorted(actual-expected),'missing':sorted(expected-actual)}
PY
git diff --cached --stat
git diff --cached -- app/game/offline/collect.py app/game/offline/collection.py app/game/offline/records.py
# Review staged documentation and synthetic smoke results before committing:
git commit -m "Preserve verbatim offline inputs and durably checkpoint attempts"
# Integrate main only after the local commit preserves the exact selected files:
git rebase github-review/main
# Stop on any conflict; do not resolve teammate code by overwriting it.
# Rerun the focused checks and public smoke, then inspect:
git diff --check github-review/main...HEAD
git diff --name-only github-review/main...HEAD
git status --short
```

After the rebase, the feature diff must contain only public-commit-files.json's paths; ignored local research evidence stays intact. No database migration or live service should be run to validate this game patch.

The following requires **separate explicit push authorization**. Inspect any existing remote branch first; do not force-push:

```sh
git ls-remote --heads github-review refs/heads/codex/research-v1-precollection-consolidated
git push -u github-review HEAD:refs/heads/codex/research-v1-precollection-consolidated
```

PR creation requires **separate explicit authorization** after the actual public branch and diff are verified. Proposed title/body are in pr-description.md. If authorized:

```sh
gh pr create --repo VasaviK-05/Multi-agent-verification --base main --head codex/research-v1-precollection-consolidated --draft --title "Preserve verbatim offline questions and durably checkpoint attempts" --body-file docs/research_v1-recording-handoff/pr-description.md
```

The latest user instruction authorizes this guarded feature-branch commit, push and PR workflow once all mandatory gates pass. Results belong in the PR description. No scientific freeze, collection authorization, main merge or teammate message follows from running Git commands.
