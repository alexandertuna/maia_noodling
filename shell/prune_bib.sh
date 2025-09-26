CODE=/ceph/users/atuna/work/maia
STEER=${CODE}/SteeringMacros/Util/steer_pruneBIB_CONDOR.py

DATA=/ceph/users/atuna/work/maia/data
BIB=${DATA}/BIB10TeV

NUM_FILES=6666
TOTAL=$((2 * ${NUM_FILES}))

for MUON in mm mp; do

    for NUM in $(seq 1 ${NUM_FILES}); do

        cp ${STEER} ./steer.py
        sed -i "s/TYPEEVENT/${MUON}/g" steer.py
        sed -i "s/INFILENAME/${NUM}/g" steer.py

        echo ${MUON} ${NUM}
        k4run steer.py --data ${DATA} > log_${MUON}_${NUM}.txt
        rm -f steer.py

    done

done | tqdm --total ${TOTAL}
