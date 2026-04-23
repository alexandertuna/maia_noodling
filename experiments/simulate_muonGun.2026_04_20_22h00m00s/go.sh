MAX_JOBS=20
CODE=/ceph/users/atuna/work/maia
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

for NUM in {110..199}; do

    # Process at most $MAX_JOBS in parallel
    while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
        echo "Waiting at $(date) ..."
        sleep 1m
    done

    echo "Launching ${NUM}"
    python digitize_muons.py --gen --sim --num ${NUM} --typeevent muonGun_pT_2p0_2p1 --events 10000 --data $(pwd) &> log_${NUM}.txt &

done

echo "Waiting!"
wait
echo "Done ^.^"
