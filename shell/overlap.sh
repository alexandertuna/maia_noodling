# https://indico.desy.de/event/36779/contributions/131996/attachments/78657/102162/221128_soft_tutorial_dd4hep.pdf

CODE=/ceph/users/atuna/work/maia
# COMPACT=${CODE}/detector-simulation-tuna/geometries/MAIA_v0/MAIA_v0.xml
COMPACT=${CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml
MACRO=${CODE}/maia_noodling/macros/overlap.mac
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)

time ddsim \
     --compactFile ${COMPACT} \
     --runType run \
     --macroFile ${MACRO} &> overlap_dump_${NOW}.txt
