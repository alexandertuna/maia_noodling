NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)
CODE=/ceph/users/atuna/work/maia
DATA=$(pwd)

# whizard ${CODE}/mucoll-benchmarks/generation/signal/whizard/mumu_H_bb_10TeV.sin

INPUT=mumu_H_bb_10TeV.hepmc
STEER=${CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py
COMPACT=${CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml
EVENTS=100

# rm -f output_sim.slcio
### warning: 100 events takes 8 hours
# ddsim --inputFile ${INPUT} \
#       --steeringFile ${STEER} \
#       --compactFile ${COMPACT} \
#       --numberOfEvents ${EVENTS} \
#       --outputFile output_sim.slcio

INPUT=output_sim.slcio
STEER_RECO=${CODE}/SteeringMacros/k4Reco/steer_reco.py
STEER_LOCAL=_steer_reco.py
TYPEEVENT=mumu_nunuh_bb
INFFILENAME=0
LOG=digi_${NOW}.txt

cp ${STEER_RECO} ${STEER_LOCAL}
sed -i "s|{the_args.data}/sim/{the_args.TypeEvent}/|./|g" ${STEER_LOCAL}
sed -i "s|{the_args.data}/reco/{the_args.TypeEvent}/|./|g" ${STEER_LOCAL}
sed -i "s|{the_args.data}/recoBIB/{the_args.TypeEvent}/|./|g" ${STEER_LOCAL}
sed -i "s|_reco_|_digi_|g" ${STEER_LOCAL}
sed -i "s|detector-simulation/geometries|k4geo/MuColl/MAIA/compact|g" ${STEER_LOCAL}

cp -a ${INPUT} ${TYPEEVENT}_sim_${INFFILENAME}.slcio

time k4run ${STEER_LOCAL} \
     -n ${EVENTS} \
     --TypeEvent ${TYPEEVENT} \
     --InFileName ${INFFILENAME} \
     --skipReco \
     --skipTrackerConing \
     --code ${CODE} \
     --data ${DATA} \
    2>&1 | tee ${LOG}
