ONE=1
TWO="42.64"
CODE=/ceph/users/atuna/work/maia
DATAMUC=/ceph/users/atuna/work/maia/data
COMPACT=/ceph/users/atuna/work/maia/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml

for ONE in {1..6667}; do

    for INVERT_Z in 0 1; do

        echo "Processing event ${ONE} with INVERT_Z=${INVERT_Z}"

        rm -f BIBinput.slcio
        time python3 ${CODE}/detector-simulation/utils/fluka_remix.py -i ${INVERT_Z} -n ${TWO} ${DATAMUC}/FLUKA/summary${ONE}_DET_IP.dat BIBinput.slcio

        cp ${CODE}/SteeringMacros/Sim/sim_steer_BIB_CONDOR.py sim_EVENT.py
        sed -i 's/OUTFILENAME/"BIB_sim.slcio"/g' sim_EVENT.py

        time ddsim --steeringFile sim_EVENT.py --inputFiles BIBinput.slcio --compactFile ${COMPACT} # -v DEBUG

        if (( INVERT_Z == 0 )); then
            LABEL="mp"
        else
            LABEL="mm"
        fi
        mv -f BIB_sim.slcio ${LABEL}_BIB_sim_${ONE}.slcio

    done

done
