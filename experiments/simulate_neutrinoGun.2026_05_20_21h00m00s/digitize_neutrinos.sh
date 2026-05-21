#!/usr/bin/env bash
set -eo pipefail

# paths
CODE=/ceph/users/atuna/work/maia
DATA=${CODE}/maia_noodling/experiments/simulate_neutrinoGun.2026_05_20_21h00m00s
TYPEEVENT="neutrinoGun"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
# source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

# run
time python digitize_muons.py --digi --bib --num ${1} --data ${DATA} --typeevent ${TYPEEVENT}
