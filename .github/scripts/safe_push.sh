#!/usr/bin/env bash
# Force-push a bot-managed branch, but never clobber manual review commits: if
# the remote branch already carries commits authored by someone other than the
# bot, skip the push and warn instead. Sourced by dependency-security-sync.yml.
safe_push() {
  local branch="$1" base="$2"
  if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
    git fetch --quiet origin "$branch"
    local human
    human=$(git log --format='%ae' "${base}..FETCH_HEAD" \
      | grep -v 'packagingApp\[bot\]' | head -n1 || true)
    if [ -n "$human" ]; then
      echo "::warning::origin/${branch} has non-bot commits (${human}); skipping force-push to preserve manual edits."
      return 0
    fi
  fi
  git push -f origin "$branch"
}
