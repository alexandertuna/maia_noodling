INPUT="/ceph/users/atuna/work/maia/data/IPairs/gen/pairs_cycle1.slcio"
STEER="/ceph/users/atuna/work/maia/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py"
COMPACT="/ceph/users/atuna/work/maia/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml"
OUTPUT="sim_pairs_cycle1.slcio"

rm -f ${OUTPUT}
ddsim --inputFile ${INPUT} \
      --steeringFile ${STEER} \
      --compactFile ${COMPACT} \
      --outputFile ${OUTPUT}
