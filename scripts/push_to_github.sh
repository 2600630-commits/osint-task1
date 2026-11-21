#!/usr/bin/env bash
# Push this repo to GitHub using a token supplied at run time.
#
# The token is read from the environment, never written to .git/config, never
# echoed, and the credential helper entry is removed again on exit.
#
#   GH_USER=<your-username> GH_TOKEN=<fine-grained PAT> GH_REPO=osint-task1 \
#       ./scripts/push_to_github.sh
#
# Token needs, on the target repo only:
#   - Contents: Read and write
#   - Metadata: Read   (automatic)
# If the repo does not exist yet, the token additionally needs
#   - Administration: Read and write   (or just create the repo by hand)

set -euo pipefail

: "${GH_USER:?set GH_USER=<your github username>}"
: "${GH_TOKEN:?set GH_TOKEN=<fine-grained personal access token>}"
GH_REPO="${GH_REPO:-osint-task1}"
GH_REMOTE="https://github.com/${GH_USER}/${GH_REPO}.git"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

cd "$(dirname "$0")/.."

cleanup() {
    git config --local --unset-all credential.helper 2>/dev/null || true
    rm -f .git/.push-creds
}
trap cleanup EXIT

# Feed credentials through a one-shot askpass-less credential store.
git config --local credential.helper "store --file=.git/.push-creds"
printf 'https://%s:%s@github.com\n' "$GH_USER" "$GH_TOKEN" > .git/.push-creds
chmod 600 .git/.push-creds

if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$GH_REMOTE"
else
    git remote add origin "$GH_REMOTE"
fi

echo "Pushing '$BRANCH' -> $GH_REMOTE"
git push -u origin "$BRANCH"
echo "Done: https://github.com/${GH_USER}/${GH_REPO}"
