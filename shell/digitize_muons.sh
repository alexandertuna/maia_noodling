CODE=/ceph/users/atuna/work/maia
TYPEEVENT="muonGun_pT_0_10"
NUM=${1}

time source ${CODE}/maia_noodling/shell/gen.sh ${NUM}
time source ${CODE}/maia_noodling/shell/sim.sh
mv output_sim.slcio ${TYPEEVENT}_sim_${NUM}.slcio
time source ${CODE}/maia_noodling/shell/digi.sh ${TYPEEVENT} ${NUM}
