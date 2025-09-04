# INPUT="/ceph/users/atuna/work/maia/data/muonGun_pT_0_50_gen.slcio"
INPUT="/ceph/users/atuna/work/maia/run/output_gen.slcio"
STEER="/ceph/users/atuna/work/maia/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py"
COMPACT="/ceph/users/atuna/work/maia/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml"

rm -f output_sim.slcio
ddsim --inputFile ${INPUT} \
      --steeringFile ${STEER} \
      --compactFile ${COMPACT} \
      --outputFile output_sim.slcio
