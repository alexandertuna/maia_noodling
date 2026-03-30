CODE=/ceph/users/atuna/work/maia
NEV=1
TYPEEVENT="ttbar"
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

MAX_JOBS=25

for EVENT in $(seq 0 99); do

    # Process at most $MAX_JOBS in parallel
    while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
        echo "Waiting at $(date) ..."
        sleep 10
    done

    STEER=steer_reco_${TYPEEVENT}_${EVENT}.py

    cp ${CODE}/SteeringMacros/k4Reco/steer_reco.py ${STEER}
    sed -i 's|{the_args.data}/sim/{the_args.TypeEvent}/|./|g' ${STEER}
    sed -i 's|{the_args.data}/reco/{the_args.TypeEvent}/|./|g' ${STEER}
    sed -i 's|{the_args.data}/recoBIB/{the_args.TypeEvent}/|./|g' ${STEER}
    # sed -i 's|_reco_|_digi_|g' ${STEER}

    time k4run ${STEER} -n ${NEV} --TypeEvent ${TYPEEVENT} --InFileName ${EVENT} --code ${CODE} --skipTrackerConing & # --skipReco
    sleep 10

done

echo "Waiting for stragglers at $(date) ..."
wait
