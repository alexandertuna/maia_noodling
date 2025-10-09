TOTAL=6666
for NUM in $(seq 1 ${TOTAL}); do
    for MUON in mm mp; do
        # mv ${MUON}_BIB_sim_${NUM}.slcio BIB10TeV/sim_${MUON}/BIB_sim_${NUM}.slcio
        mv ${MUON}_pruned_BIB_sim_${NUM}.slcio BIB10TeV/sim_${MUON}_pruned/BIB_sim_${NUM}.slcio
    done
done
