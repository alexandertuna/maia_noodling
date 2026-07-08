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
    echo "Usage: $0 <seed> <output_tag>"
    exit 1
fi
if [ -z "$2" ]; then
    echo "Usage: $0 <seed> <output_tag>"
    exit 1
fi
SEED=$1
NOW=$2
echo "Args: SEED=${SEED} NOW=${NOW}"

# variables
CODE=/ceph/users/atuna/work/maia
THISDIR=${CODE}/maia_noodling/experiments/simulate_ttbar.2026_07_08_10h14m00s
INPUT=${THISDIR}/hepmc/ttbar_${SEED}.hepmc
STEER=${CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py
COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
EVENTS_PER_JOB=10
# NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)

# run simulation
time ddsim --inputFile ${INPUT} \
     --steeringFile ${STEER} \
     --compactFile ${COMPACT} \
     --numberOfEvents ${EVENTS_PER_JOB} \
     --outputFile ttbar_sim_${NOW}_${SEED}.slcio

echo "Done! ^.^"
