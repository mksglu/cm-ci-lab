#!/usr/bin/env bash
# One triage task: a real merged bug-fix PR of a high-star repo, with the fix reverted so the tests fail again.
# Usage: bash lab/triage-task.sh <task>   (run from the lab checkout; writes the repo to $RUNNER_TEMP/repo)
# Writes TASK_LANG, TASK_TEST (the real test command), TASK_TESTFILES to $GITHUB_ENV.
# The result is a one-commit snapshot with no history, so the model cannot read the upstream fix from git.
set -euo pipefail
task="$1"
case "$task" in
  requests) repo=psf/requests;           sha=47914226c2968802f2cdee3f6f0f6e06e4472f64; lang=python
            src=(src/requests/utils.py);  tests=(tests/test_utils.py)
            test="python -m pytest tests -v -p no:cacheprovider"; install="pip install -q -e '.[test]'" ;;
  flask)    repo=pallets/flask;          sha=05e9c6bd630ecf4ec0ec884b1fc7901663737bc7; lang=python
            src=(src/flask/app.py src/flask/testing.py); tests=(tests/test_basic.py tests/test_testing.py)
            test="python -m pytest tests -v -p no:cacheprovider"; install="pip install -q -e . pytest asgiref python-dotenv" ;;
  express)  repo=expressjs/express;      sha=9a34acf03cb818ff3f8bc40e44176e277a25cbb9; lang=node
            src=(lib/response.js);        tests=(test/res.send.js)
            test="npm test"; install="npm install --no-audit --no-fund --loglevel=error" ;;
  koa)      repo=koajs/koa;              sha=b786e7b456782c2cff1d6549cd4c8dba3feeb262; lang=node
            src=(lib/application.js);     tests=(__tests__/context/assert.test.js)
            test="npm test"; install="npm install --no-audit --no-fund --loglevel=error" ;;
  cobra)    repo=spf13/cobra;            sha=746ef07158728502482cea9f880a6f4b21ef29a9; lang=go
            src=(completions.go);         tests=(completions_test.go)
            test="go test -v ./..."; install="go mod download" ;;
  ripgrep)  repo=BurntSushi/ripgrep;     sha=de2567a4c76fa671005538d6cd841abc44932b9a; lang=rust
            src=(crates/printer/src/util.rs); tests=(tests/regression.rs)
            test="cargo test --color never"; install="true" ;;
  *) echo "unknown task $task"; exit 2 ;;
esac
d="$RUNNER_TEMP/repo"; rm -rf "$d"
git clone -q --filter=blob:none "https://github.com/$repo" "$d"
cd "$d"
git checkout -q "$sha"
git checkout -q "$sha^" -- "${src[@]}"          # revert the fix, keep the new tests
rm -rf .git; git init -q; git add -A
git -c user.name=lab -c user.email=lab@example.com commit -q -m "snapshot: CI failing"
git diff --stat HEAD | tail -1 || true
{ echo "TASK_LANG=$lang"; echo "TASK_TEST=$test"; echo "TASK_INSTALL=$install"; echo "TASK_TESTFILES=${tests[*]}"; echo "TASK_SRC=${src[*]}"; } >> "$GITHUB_ENV"
echo "task=$task repo=$repo sha=${sha:0:8} test=$test"
