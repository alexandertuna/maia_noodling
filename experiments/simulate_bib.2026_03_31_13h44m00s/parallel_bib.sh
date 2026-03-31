#!/usr/bin/env bash
set -eo pipefail

# constants
ONE="1"
BIBINPUT=bibinput_${ONE}.slcio
CODE=/ceph/users/atuna/work/maia
DATAMUC=/ceph/users/atuna/work/maia/data
# COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
COMPACT=${CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)
echo "CODE=${CODE}"
echo "DATAMUC=${DATAMUC}"
echo "COMPACT=${COMPACT}"
echo "NOW=${NOW}"


# process
for SIM_EVENT in sim_EVENT_1keV.py sim_EVENT_1keV_seed.py sim_EVENT_baseline.py sim_EVENT_None.py sim_EVENT_None_seed.py; do

    time ddsim --steeringFile ${SIM_EVENT} --inputFiles ${BIBINPUT} --compactFile ${COMPACT} &

done

echo "Launched all simulations, waiting for them to finish ..."
wait
echo "All simulations finished ^.^"
