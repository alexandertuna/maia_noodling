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
TYPEEVENT="muonGun_pT_0_10"
NUM=${1}
echo "CODE=${CODE}"
echo "TYPEEVENT=${TYPEEVENT}"
echo "NUM=${NUM}"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

# run
time source ${CODE}/maia_noodling/shell/gen.sh ${NUM}
time source ${CODE}/maia_noodling/shell/sim.sh
mv output_sim.slcio ${TYPEEVENT}_sim_${NUM}.slcio
time source ${CODE}/maia_noodling/shell/digi.sh ${TYPEEVENT} ${NUM}
rm -f output_gen.slcio
