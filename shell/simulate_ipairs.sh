#!/usr/bin/env bash
set -eo pipefail

NUM=${1}

CODE="/ceph/users/atuna/work/maia"
DATA="/ceph/users/atuna/work/maia/data"

# STEER="${CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py"
# COMPACT="${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml"

INPUT="${DATA}/IPairs/gen/pairs_cycle${NUM}.slcio"
STEER="${CODE}/SteeringMacros/Sim/sim_steer_BIB_CONDOR.py"
COMPACT="${CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
OUTPUT="sim_pairs_cycle${NUM}.slcio"

echo $OUTPUT

rm -f ${OUTPUT}
ddsim --inputFile ${INPUT} \
      --steeringFile ${STEER} \
      --compactFile ${COMPACT} \
      --outputFile ${OUTPUT}
