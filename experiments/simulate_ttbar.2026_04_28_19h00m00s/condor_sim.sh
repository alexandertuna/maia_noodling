#!/usr/bin/env bash
set -eo pipefail

# info
echo "SHELL=$SHELL"
echo "PWD=$PWD"
echo "HOST=$(hostname)"

# env (setup_mucoll)
echo "Setting up environment..."
source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh

# variables
CODE=/ceph/users/atuna/work/maia
THISDIR=${CODE}/maia_noodling/experiments/simulate_ttbar.2026_04_28_19h00m00s
TOTAL_EVENTS="1000"
INPUT=${THISDIR}/events_${TOTAL_EVENTS}.hepmc
STEER=${CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py
COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
EVENTS_PER_JOB=1
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)

# check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <skip_n_events>"
    exit 1
fi
SKIP_N_EVENTS=$1
echo "Args: SKIP_N_EVENTS=${SKIP_N_EVENTS}"

# run simulation
time ddsim --inputFile ${INPUT} \
     --steeringFile ${STEER} \
     --compactFile ${COMPACT} \
     --numberOfEvents ${EVENTS_PER_JOB} \
     --skipNEvents ${SKIP_N_EVENTS} \
     --outputFile ttbar_sim_${NOW}_${SKIP_N_EVENTS}.slcio

echo "Done! ^.^"
