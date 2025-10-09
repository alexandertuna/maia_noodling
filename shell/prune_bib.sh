#!/usr/bin/env bash
set -eo pipefail

# preamble
echo "SHELL=$SHELL"
echo "PWD=$PWD"
echo "HOST=$(hostname)"
which python || true
python --version || true
echo "env"
env
echo "ls ./"
ls ./

# constants
CODE=/ceph/users/atuna/work/maia
STEER=${CODE}/SteeringMacros/Util/steer_pruneBIB_CONDOR.py
DATA=${CODE}/maia_noodling/experiments/simulate_bib.2025_10_08_09h35m49s
echo "CODE=${CODE}"
echo "STEER=${STEER}"
echo "DATA=${DATA}"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

# run
NUM=${1}
for MUON in mm mp; do

    LOCAL=steer_${MUON}_${NUM}.py
    cp ${STEER} ${LOCAL}
    sed -i "s/TYPEEVENT/${MUON}/g" ${LOCAL}
    sed -i "s/INFILENAME/${NUM}/g" ${LOCAL}

    # bonus sed because condor cant write to /ceph
    TEXT_FROM="{the_args.data}/BIB10TeV/sim_${MUON}_pruned/BIB_sim_${NUM}.slcio"
    TEXT_TO="${MUON}_pruned_BIB_sim_${NUM}.slcio"
    sed -i "s|${TEXT_FROM}|${TEXT_TO}|g" ${LOCAL}

    echo ${MUON} ${NUM}
    k4run ${LOCAL} --data ${DATA}
    rm -f ${LOCAL}

done

