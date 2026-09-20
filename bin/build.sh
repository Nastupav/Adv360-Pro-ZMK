#!/usr/bin/env bash

set -euo pipefail

project_dir=$(pwd)
timestamp=${TIMESTAMP:-$(date -u +%Y%m%d%H%M)}
commit="${COMMIT:-xxxxxx}"
build_right="${BUILD_RIGHT:-true}"
prefix="adv360-${timestamp}-${commit}"

mkdir -p firmware
# Capture the exact dependency graph and effective settings alongside each pair.
west manifest --freeze --active-only > "firmware/${prefix}-manifest.yml"
artifacts=("${prefix}-manifest.yml" "${prefix}-source.tar.gz")
# Archive the exact config used, including uncommitted local changes.
tar -czf "firmware/${prefix}-source.tar.gz" -C config .

west build -s zmk/app -p -d build/left -b adv360_left -- \
    -DZMK_CONFIG="${project_dir}/config"
cp build/left/zephyr/zmk.uf2 "firmware/${prefix}-left.uf2"

artifacts+=("${prefix}-left.uf2" "${prefix}-left.config")
cp build/left/zephyr/.config "firmware/${prefix}-left.config"

if [[ "${build_right}" == true ]]; then
    west build -s zmk/app -p -d build/right -b adv360_right -- \
        -DZMK_CONFIG="${project_dir}/config"
    cp build/right/zephyr/zmk.uf2 "firmware/${prefix}-right.uf2"
    artifacts+=("${prefix}-right.uf2" "${prefix}-right.config")
    cp build/right/zephyr/.config "firmware/${prefix}-right.config"
fi

(
    cd firmware
    sha256sum "${artifacts[@]}" > SHA256SUMS
)

printf 'Firmware written to %s/firmware\n' "${project_dir}"
