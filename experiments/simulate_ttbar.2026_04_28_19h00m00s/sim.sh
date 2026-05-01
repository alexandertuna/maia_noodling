CODE=/ceph/users/atuna/work/maia
THISDIR=${CODE}/maia_noodling/experiments/simulate_ttbar.2026_04_28_19h00m00s
TOTAL_EVENTS="1000"
INPUT=${THISDIR}/events_${TOTAL_EVENTS}.hepmc
STEER=${CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py
COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
EVENTS_PER_JOB=10
MAX_JOBS=10
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)

for SKIP_N_EVENTS in $(seq 0 ${EVENTS_PER_JOB} ${TOTAL_EVENTS}); do

    # Process at most $MAX_JOBS in parallel
    while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
        echo "Waiting at $(date) ..."
        sleep 10
    done

    # rm -f output_sim.slcio
    time ddsim --inputFile ${INPUT} \
               --steeringFile ${STEER} \
               --compactFile ${COMPACT} \
               --numberOfEvents ${EVENTS_PER_JOB} \
               --skipNEvents ${SKIP_N_EVENTS} \
               --outputFile ttbar_sim_${NOW}_${SKIP_N_EVENTS}.slcio \
               2>&1 | tee log_${NOW}_${SKIP_N_EVENTS}.txt &

    sleep 10

done

echo "Waiting for stragglers at $(date) ..."
wait

