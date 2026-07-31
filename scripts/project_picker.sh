#!/usr/bin/env bash

set -euo pipefail

roots=("${HOME}/github" "${HOME}/Desktop")
existing=()
for root in "${roots[@]}"; do
    [[ -d "${root}" ]] && existing+=("${root}")
done

if (( ${#existing[@]} == 0 )); then
    printf 'No project roots found.\n' >&2
    exit 1
fi

project=$(
    find "${existing[@]}" -mindepth 1 -maxdepth 5 -type d -name .git -prune -print 2>/dev/null |
        sed 's#/.git$##' |
        sort -u |
        fzf --prompt='project> ' --height=100% --reverse
)

[[ -n "${project}" ]] || exit 0
session=$(basename "${project}" | tr -cs '[:alnum:]_-' '_')

if [[ -n "${TMUX:-}" ]]; then
    tmux new-session -Ad -s "${session}" -c "${project}"
    tmux switch-client -t "${session}"
else
    tmux new-session -A -s "${session}" -c "${project}"
fi
