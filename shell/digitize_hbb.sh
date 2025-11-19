#!/usr/bin/env bash
set -eo pipefail

# paths
CODE=/ceph/users/atuna/work/maia
DATA=/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2025_10_17_10h40m00s
# DATA=/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_hbb.2025_11_05_17h57m00s

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

# run
time python ${CODE}/maia_noodling/python/digitize_muons.py --gen --sim --digi --num ${1} --data ${DATA} --bib --typeevent mumu_H_bb_10TeV
