CODE=/ceph/users/atuna/work/maia
# COMPACT=${CODE}/detector-simulation-tuna/geometries/MAIA_v0/MAIA_v0.xml
COMPACT=${CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml
time ${CODE}/k4geo/utils/dd4hep2root.py -c ${COMPACT} -o geo.root
