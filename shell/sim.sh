CODE=/ceph/users/atuna/work/maia

# INPUT="${CODE}/data/muonGun_pT_0_50_gen.slcio"
INPUT="output_gen.slcio"
STEER=${CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py
# COMPACT=${CODE}/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml
COMPACT=${CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml
EVENTS=10

rm -f output_sim.slcio
ddsim --inputFile ${INPUT} \
      --steeringFile ${STEER} \
      --compactFile ${COMPACT} \
      --numberOfEvents ${EVENTS} \
      --outputFile output_sim.slcio
