CODE=/ceph/users/atuna/work/maia

INPUT="events.hepmc"
STEER=${CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py
COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
NUMBER_OF_EVENTS=10
MAX_JOBS=25
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)

for SKIP_N_EVENTS in $(seq 0 ${NUMBER_OF_EVENTS} 99); do

    # Process at most $MAX_JOBS in parallel
    while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
        echo "Waiting at $(date) ..."
        sleep 10
    done

    # rm -f output_sim.slcio
    time ddsim --inputFile ${INPUT} \
               --steeringFile ${STEER} \
               --compactFile ${COMPACT} \
               --numberOfEvents ${NUMBER_OF_EVENTS} \
               --skipNEvents ${SKIP_N_EVENTS} \
               --outputFile ttbar_sim_${NOW}_${SKIP_N_EVENTS}.slcio \
               2>&1 | tee log_${NOW}_${SKIP_N_EVENTS}.txt &

    sleep 10

done

echo "Waiting for stragglers at $(date) ..."
wait

