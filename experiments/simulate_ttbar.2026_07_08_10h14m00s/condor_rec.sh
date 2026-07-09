#!/usr/bin/env bash
set -eo pipefail

# info
echo "SHELL=$SHELL"
echo "PWD=$PWD"
echo "HOST=$(hostname)"

# env (setup_mucoll)
echo "Setting up environment..."
source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh

# check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <event> <sim_data_dir>"
    exit 1
fi
if [ -z "$2" ]; then
    echo "Usage: $0 <event> <sim_data_dir>"
    exit 1
fi
EVENT=$1
SIM_DATA_DIR=$2
echo "Args: EVENT=${EVENT} SIM_DATA_DIR=${SIM_DATA_DIR}"

# variables
CODE=/ceph/users/atuna/work/maia
TYPEEVENT="ttbar"
export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

# locate the steering file
STEER=${SIM_DATA_DIR}/steer_reco_${TYPEEVENT}.py

# copy data locally
mkdir -p ./tmp/
DATA_FNAME=${TYPEEVENT}_sim_${EVENT}.slcio
cp -a ${SIM_DATA_DIR}/${DATA_FNAME} ./tmp/${DATA_FNAME}

# run
time k4run ${STEER} --TypeEvent ${TYPEEVENT} --InFileName ${EVENT} --code ${CODE} --skipTrackerConing # 2>&1 | tee log_${NOW}.txt &

# mv
rm -rf ./tmp/
