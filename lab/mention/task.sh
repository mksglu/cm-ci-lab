#!/usr/bin/env bash
# Mention-assistant / issue-to-PR task: a real merged bug-fix PR (>=20k stars) that closes a linked issue.
# The repo is the PARENT of the merge commit (the bug is present, the fix and its tests are absent), as one commit with no
# history. The PR's own test files are held back in $RUNNER_TEMP/hidden and copied in only at check time.
# CONTROL=1 also copies the upstream source fix in (the suite must pass: task validity). Usage: bash lab/mention/task.sh <task>
set -euo pipefail
task="$1"
case "$task" in
  flask)   repo=pallets/flask;      sha=05e9c6bd630ecf4ec0ec884b1fc7901663737bc7; lang=python
           src=(src/flask/app.py src/flask/testing.py); tests=(tests/test_basic.py tests/test_testing.py)
           test="python -m pytest tests -v -p no:cacheprovider"; install="pip install -q -e . pytest asgiref python-dotenv" ;;
  cobra)   repo=spf13/cobra;        sha=746ef07158728502482cea9f880a6f4b21ef29a9; lang=go
           src=(completions.go);    tests=(completions_test.go)
           test="go test -v ./..."; install="go mod download" ;;
  ripgrep) repo=BurntSushi/ripgrep; sha=de2567a4c76fa671005538d6cd841abc44932b9a; lang=rust
           src=(crates/printer/src/util.rs); tests=(tests/regression.rs)
           test="cargo test --color never"; install="true" ;;
  rich)    repo=Textualize/rich;    sha=59b1aca63bf9ec69ada93af960d8b2a7bd920477; lang=python
           src=(rich/_wrap.py rich/cells.py); tests=(tests/test_cells.py tests/test_text.py)
           test="python -m pytest tests -v -p no:cacheprovider"; install="pip install -q -e . pytest attrs 'setuptools<81' 'pygments==2.17.2'" ;;
  chalk)   repo=chalk/chalk;        sha=e91293130c7d642c7b91152c3c942743a3b910a7; lang=node
           src=(source/vendor/supports-color/index.js); tests=(test/_force-color-fixture.js test/force-color.js)
           test="npm test"; install="npm install --no-audit --no-fund --loglevel=error" ;;
  gin)     repo=gin-gonic/gin;      sha=ea9fab99e01d55a5e4f8daacc0d11ccffaee0a15; lang=go
           src=(tree.go);           tests=(routes_test.go)
           test="go test -v ./..."; install="go mod download" ;;
  fd)      repo=sharkdp/fd;         sha=3c784f63b8e7976650682d550926bb79e9e1f640; lang=rust
           src=(src/cli.rs src/main.rs); tests=(tests/tests.rs)
           test="cargo test --color never"; install="true" ;;
  dayjs)   repo=iamkun/dayjs;       sha=dad46e6fe5198d77d87ed3b121937f77adaee0a6; lang=node
           src=(src/plugin/timezone/index.js); tests=(test/plugin/timezone.test.js)
           test="TZ=Europe/Paris npx jest test/plugin/timezone.test --coverage=false"; install="npm install --no-audit --no-fund --loglevel=error" ;;
  tqdm)    repo=tqdm/tqdm;          sha=9cf5a12b1f955468a17f0ba3c59092b23e4258ac; lang=python
           src=(tqdm/contrib/concurrent.py); tests=(tests/tests_concurrent.py)
           test="python -m pytest tests/tests_concurrent.py -p no:cacheprovider"; install="pip install -q -e . pytest pytest-timeout pytest-asyncio" ;;
  testify) repo=stretchr/testify;   sha=246de4504b1b5990508c5ab6b34fbcbd16614095; lang=go
           src=(assert/assertions.go); tests=(assert/assertions_test.go)
           test="go test ./assert/..."; install="go mod download" ;;
  loguru)  repo=Delgan/loguru;      sha=5672e7d0ad610d70c5e549939b049303edefda19; lang=python
           src=(loguru/_datetime.py); tests=(tests/test_datetime.py)
           test="python -m pytest tests/test_datetime.py -p no:cacheprovider"; install="pip install -q -e . pytest freezegun" ;;
  chi)     repo=go-chi/chi;         sha=9b6ddcddb96aa14648702e7eaabef38e14e65157; lang=go
           src=(tree.go);           tests=(mux_test.go)
           test="go test ./..."; install="go mod download" ;;
  *) echo "unknown task $task"; exit 2 ;;
esac
up="$RUNNER_TEMP/up"; d="$RUNNER_TEMP/repo"; h="$RUNNER_TEMP/hidden"; f="$RUNNER_TEMP/fix"
rm -rf "$up" "$d" "$h" "$f"; mkdir -p "$h" "$f"
git clone -q --filter=blob:none "https://github.com/$repo" "$up"
cd "$up"
for p in "${tests[@]}"; do mkdir -p "$h/$(dirname "$p")"; git show "$sha:$p" > "$h/$p"; done
for p in "${src[@]}";   do mkdir -p "$f/$(dirname "$p")"; git show "$sha:$p" > "$f/$p"; done
git checkout -q "$sha^"
cp -R "$up" "$d"; rm -rf "$up"            # no upstream clone is left on the runner
cd "$d"; rm -rf .git; git init -q; git add -A
git -c user.name=lab -c user.email=lab@example.com commit -q -m "snapshot"
{ echo "TASK_LANG=$lang"; echo "TASK_TEST=$test"; echo "TASK_INSTALL=$install"; echo "TASK_TESTFILES=${tests[*]}"; echo "TASK_SRC=${src[*]}"
  echo "SNAP=$(git rev-parse HEAD)"; echo "TASK_REPO=$repo"; } >> "$GITHUB_ENV"
echo "task=$task repo=$repo parent-of=${sha:0:8} test=$test"
