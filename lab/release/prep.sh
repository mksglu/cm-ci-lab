#!/usr/bin/env bash
# Builds the repo the agent works in: full history up to the new tag and nothing newer.
#  - fetches only the new tag (and the previous tag), so no later commits or tags exist locally;
#  - removes the remote, so git cannot fetch the answer;
#  - rewrites prev..tag so changelog / release-notes files keep their previous-tag content in every commit,
#    so the published notes cannot be read from the tree, "git diff", "git log -p" or "git show".
# Usage: bash lab/release/prep.sh <task>   Writes REL_* to $GITHUB_ENV, repo to $RUNNER_TEMP/repo.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/tasks.sh"; release_task "$1"
d="$RUNNER_TEMP/repo"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
git init -q
git remote add origin "https://github.com/$REL_REPO"
git fetch -q --no-tags origin "refs/tags/$REL_TAG:refs/tags/$REL_TAG" "refs/tags/$REL_PREV:refs/tags/$REL_PREV"
git checkout -q --detach "refs/tags/$REL_TAG"
tagsha=$(git rev-parse HEAD)
git merge-base --is-ancestor "$REL_PREV" "$REL_TAG" && anc=yes || anc=no
# Changelog / release-notes files at the new tag. Every commit in prev..tag gets these files pinned to their
# previous-tag content (or removed if absent there), so no diff, log -p or show can reveal the published notes.
: > "$RUNNER_TEMP/restored-changelogs.txt"
git ls-files | while IFS= read -r f; do
  low=$(printf '%s' "$f" | tr 'A-Z' 'a-z'); b=${low##*/}
  hit=0
  case "$low" in *changelog*|*release-notes*|*release_notes*|*releasenotes*) hit=1 ;; esac
  case "$b" in changes|changes.md|changes.rst|changes.txt|history|history.md|history.rst|news|news.md|news.rst|releases.md) hit=1 ;; esac
  [ "$hit" = 1 ] && echo "$f" >> "$RUNNER_TEMP/restored-changelogs.txt"
done || true
git ls-tree -r "$REL_PREV" | while IFS=$'\t' read -r meta path; do
  if grep -qxF -- "$path" "$RUNNER_TEMP/restored-changelogs.txt"; then set -- $meta; echo "$1 $3 $path"; fi
done > "$RUNNER_TEMP/prev-pins.txt" || true
removed=$(wc -l < "$RUNNER_TEMP/restored-changelogs.txt" | tr -d ' ')
cat > "$RUNNER_TEMP/index-filter.sh" <<'IF'
#!/usr/bin/env bash
while IFS= read -r f; do git update-index --force-remove -- "$f"; done < "$RT/restored-changelogs.txt"
while read -r mode blob path; do
  git update-index --add --cacheinfo "$mode,$blob,$path"
done < "$RT/prev-pins.txt"
IF
chmod +x "$RUNNER_TEMP/index-filter.sh"
export RT="$RUNNER_TEMP" FILTER_BRANCH_SQUELCH_WARNING=1
git -c user.name=lab -c user.email=lab@example.com filter-branch -f --index-filter "$RUNNER_TEMP/index-filter.sh" "refs/tags/$REL_PREV..HEAD" >/dev/null 2>&1
rm -rf .git/refs/original
git tag -d "$REL_TAG" >/dev/null
git remote remove origin
ncommits=$(git rev-list --count "$REL_PREV..HEAD")
echo "task=$1 repo=$REL_REPO tag=$REL_TAG prev=$REL_PREV prev_is_ancestor=$anc commits=$ncommits changelog_files_reset=$removed tagsha=${tagsha:0:8}"
git diff --stat "$REL_PREV" HEAD | tail -1 || true
{ echo "REL_REPO=$REL_REPO"; echo "REL_TAG=$REL_TAG"; echo "REL_PREV=$REL_PREV"; echo "REL_NAME=$REL_NAME"; echo "REL_COMMITS=$ncommits"; echo "REL_ANCESTOR=$anc"; echo "REL_CHANGELOGS_RESET=$removed"; } >> "$GITHUB_ENV"
