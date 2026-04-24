TOTAL=6666

mkdir -p BIB10TeV/sim_mm
mkdir -p BIB10TeV/sim_mp
for NUM in $(seq 1 ${TOTAL}); do
    for MUON in mm mp; do
        mv ${MUON}_BIB_sim_${NUM}.slcio BIB10TeV/sim_${MUON}/BIB_sim_${NUM}.slcio
    done
done

# mkdir -p BIB10TeV/sim_mm_pruned
# mkdir -p BIB10TeV/sim_mp_pruned
# for NUM in $(seq 1 ${TOTAL}); do
#     for MUON in mm mp; do
#         mv ${MUON}_pruned_BIB_sim_${NUM}.slcio BIB10TeV/sim_${MUON}_pruned/BIB_sim_${NUM}.slcio
#     done
# done
