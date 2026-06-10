#!/usr/bin/env bash
set -eo pipefail

# paths
CODE=/ceph/users/atuna/work/maia
# DATA=${CODE}/maia_noodling/experiments/simulate_bib.2026_01_07_22h00m00s # v01
DATA=${CODE}/maia_noodling/experiments/simulate_bib.2026_05_14_12h00m00s # v05
TYPEEVENT="neutrinoGun"
# RESOLUTIONUV="0.000"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
# source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

for RESOLUTIONUV in 0.000 0.005 0.010 0.020; do

    mkdir -p ${RESOLUTIONUV}

    for NUM in $(seq 0 9); do

        # run
        echo "Running ${RESOLUTIONUV} ${NUM} ..."
        time python digitize_muons.py \
             --gen \
             --sim \
             --digi \
             --bib \
             --num ${NUM} \
             --ResolutionUV ${RESOLUTIONUV} \
             --data ${DATA} \
             --typeevent ${TYPEEVENT} &> neutrinoGun_log_${NUM}.txt

        echo "Moving ..."
        mv neutrinoGun_*  ${RESOLUTIONUV}/

    done

done

echo "Done ^.^"
