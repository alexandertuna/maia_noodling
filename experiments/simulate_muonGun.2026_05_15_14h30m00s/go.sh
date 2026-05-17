MAX_JOBS=10
EVENTS=10000
CODE=/ceph/users/atuna/work/maia
SIM_DIR=${CODE}/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/
TYPEEVENT=muonGun_pT_2p0_2p1
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

for NUM in {300..349}; do

    # Process at most $MAX_JOBS in parallel
    while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
        echo "Waiting at $(date) ..."
        sleep 1m
    done

    echo "Launching ${NUM}"
    cp -a ${SIM_DIR}/${TYPEEVENT}_sim_${NUM}.slcio ./
    python digitize_muons.py --digi --num ${NUM} --typeevent ${TYPEEVENT} --events ${EVENTS} --data $(pwd) # &> log_${NUM}.txt &

done

echo "Waiting!"
wait
echo "Done ^.^"
