#!/usr/bin/env bash

set -euo pipefail

project_dir=$(pwd)
commit="${COMMIT:-unknown}"
config_hash="${CONFIG_HASH:-unknown}"
dirty_suffix="${DIRTY_SUFFIX:-}"
build_right="${BUILD_RIGHT:-true}"
prefix="adv360-${commit}-${config_hash}${dirty_suffix}"

mkdir -p firmware

west build -s zmk/app -p -d build/left -b adv360_left -- \
    -DZMK_CONFIG="${project_dir}/config"
cp build/left/zephyr/zmk.uf2 "firmware/${prefix}-left.uf2"

artifacts=("${prefix}-left.uf2")

if [[ "${build_right}" == true ]]; then
    west build -s zmk/app -p -d build/right -b adv360_right -- \
        -DZMK_CONFIG="${project_dir}/config"
    cp build/right/zephyr/zmk.uf2 "firmware/${prefix}-right.uf2"
    artifacts+=("${prefix}-right.uf2")
else
    # A prior full build can have the same commit/fingerprint prefix. Do not
    # leave that stale right artifact beside a manifest declaring right=false.
    rm -f "firmware/${prefix}-right.uf2"
fi

(
    cd firmware
    printf '%s\n' "${artifacts[@]}" | sort | xargs sha256sum > SHA256SUMS
)

right_json=false
if [[ "${build_right}" == true ]]; then right_json=true; fi
printf '{\n  "schema": 1,\n  "commit": "%s",\n  "config_sha256": "%s",\n  "dirty": %s,\n  "left": true,\n  "right": %s\n}\n' \
    "${commit}" "${config_hash}" "$([[ -n "${dirty_suffix}" ]] && printf true || printf false)" "${right_json}" \
    > firmware/build-manifest.json

printf 'Firmware written to %s/firmware\n' "${project_dir}"
