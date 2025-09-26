CODE=/ceph/users/atuna/work/maia
COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
MACRO=${CODE}/maia_noodling/macros/overlap.mac
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)

time ddsim \
     --compactFile ${COMPACT} \
     --runType run \
     --macroFile ${MACRO} > overlap_dump_${NOW}.txt
