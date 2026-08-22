#!/usr/bin/env bash

set -euo pipefail

project_dir=$(pwd)
timestamp=${TIMESTAMP:-$(date -u +%Y%m%d%H%M)}
commit="${COMMIT:-xxxxxx}"
build_right="${BUILD_RIGHT:-true}"
prefix="adv360-${timestamp}-${commit}"

mkdir -p firmware

west build -s zmk/app -p -d build/left -b adv360_left -S studio-rpc-usb-uart -- \
    -DZMK_CONFIG="${project_dir}/config" \
    -DCONFIG_ZMK_STUDIO=y
cp build/left/zephyr/zmk.uf2 "firmware/${prefix}-left.uf2"

artifacts=("${prefix}-left.uf2")

if [[ "${build_right}" == true ]]; then
    west build -s zmk/app -p -d build/right -b adv360_right -- \
        -DZMK_CONFIG="${project_dir}/config"
    cp build/right/zephyr/zmk.uf2 "firmware/${prefix}-right.uf2"
    artifacts+=("${prefix}-right.uf2")
fi

(
    cd firmware
    sha256sum "${artifacts[@]}" > SHA256SUMS
)

printf 'Firmware written to %s/firmware\n' "${project_dir}"
