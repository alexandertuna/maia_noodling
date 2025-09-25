#!/usr/bin/env bash
set -eo pipefail

NUM=${1}
INPUT="/ceph/users/atuna/work/maia/data/IPairs/gen/pairs_cycle${NUM}.slcio"
# STEER="/ceph/users/atuna/work/maia/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py"
STEER="/ceph/users/atuna/work/maia/SteeringMacros/Sim/sim_steer_BIB_CONDOR.py"
COMPACT="/ceph/users/atuna/work/maia/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml"
OUTPUT="sim_pairs_cycle${NUM}.slcio"

echo $OUTPUT

rm -f ${OUTPUT}
ddsim --inputFile ${INPUT} \
      --steeringFile ${STEER} \
      --compactFile ${COMPACT} \
      --outputFile ${OUTPUT}
