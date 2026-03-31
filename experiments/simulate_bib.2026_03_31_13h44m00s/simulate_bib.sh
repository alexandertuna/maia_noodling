#!/usr/bin/env bash
set -eo pipefail

# preamble
echo "SHELL=$SHELL"
echo "PWD=$PWD"
echo "HOST=$(hostname)"
which python || true
python --version || true
echo "ls ./"
ls ./

# constants
ONE="1"
TWO="42.64"
CODE=/ceph/users/atuna/work/maia
DATAMUC=/ceph/users/atuna/work/maia/data
# COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
COMPACT=${CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)
echo "CODE=${CODE}"
echo "DATAMUC=${DATAMUC}"
echo "COMPACT=${COMPACT}"
echo "NOW=${NOW}"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
### source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
### export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

# process
for INVERT_Z in 0; do

    # mu-plus and mu-minus
    if (( INVERT_Z == 0 )); then
        LABEL="mp"
    else
        LABEL="mm"
    fi
    echo "Processing ${ONE} with INVERT_Z=${INVERT_Z} -> LABEL=${LABEL}"

    BIBINPUT=bibinput_${ONE}.slcio
    if [ ! -f "${BIBINPUT}" ]; then
        echo "Running fluka_remix.py"
        time python3 ${CODE}/detector-simulation/utils/fluka_remix.py -i ${INVERT_Z} -n ${TWO} ${DATAMUC}/FLUKA/summary${ONE}_DET_IP.dat ${BIBINPUT}
    fi

    if [ ! -f "sim_EVENT.py" ]; then
        echo "Copying sim_EVENT.py locally"
        cp ${CODE}/SteeringMacros/Sim/sim_steer_BIB_CONDOR.py ./sim_EVENT.py
        sed -i 's/OUTFILENAME/"BIB_sim.slcio"/g' sim_EVENT.py
    fi

    time ddsim --steeringFile sim_EVENT.py --inputFiles ${BIBINPUT} --compactFile ${COMPACT}
    mv -f BIB_sim.slcio ${LABEL}_BIB_sim_${ONE}_${NOW}.slcio
    ### rm -f ${BIBINPUT} sim_EVENT.py

done
