ONE=1
TWO="42.64"
CODE=/ceph/users/atuna/work/maia
DATAMUC=/ceph/users/atuna/work/maia/data
# SUMMARY_0=${DATAMUC}/FLUKA/summary$((ONE+0))_DET_IP.dat
# SUMMARY_1=${DATAMUC}/FLUKA/summary$((ONE+1))_DET_IP.dat
# SUMMARY_2=${DATAMUC}/FLUKA/summary$((ONE+2))_DET_IP.dat
# SUMMARY_3=${DATAMUC}/FLUKA/summary$((ONE+3))_DET_IP.dat
# SUMMARY_4=${DATAMUC}/FLUKA/summary$((ONE+4))_DET_IP.dat
COMPACT=/ceph/users/atuna/work/maia/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml

for INVERT_Z in 0 1; do

    rm -f BIBinput.slcio
    time python3 ${CODE}/detector-simulation/utils/fluka_remix.py -i ${INVERT_Z} -n ${TWO} ${DATAMUC}/FLUKA/summary${ONE}_DET_IP.dat BIBinput.slcio

    cp ${CODE}/SteeringMacros/Sim/sim_steer_BIB_CONDOR.py sim_EVENT_${ONE}.py
    sed -i 's/OUTFILENAME/"BIB_sim.slcio"/g' sim_EVENT_${ONE}.py

    time ddsim --steeringFile sim_EVENT_${ONE}.py --inputFiles BIBinput.slcio --compactFile ${COMPACT} # -v DEBUG

    if (( INVERT_Z == 0 )); then
        LABEL="mp"
    else
        LABEL="mm"
    fi
    mv -f BIB_sim.slcio ${LABEL}_BIB_sim_${ONE}.slcio

done
