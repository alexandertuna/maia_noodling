MAX_JOBS=10
CODE=/ceph/users/atuna/work/maia

for NUM in {100..100}; do

    # Process at most $MAX_JOBS in parallel
    while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
        echo "Waiting at $(date) ..."
        sleep 1m
    done

    echo "Launching ${NUM}"
    python digitize_muons.py --gen --sim --num ${NUM} --typeevent muonGun_pT_2p0_2p1 --events 1000 --data $(pwd) # &> log_${NUM}.txt &

done

echo "Waiting!"
wait
echo "Done ^.^"
