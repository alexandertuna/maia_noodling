CODE=/ceph/users/atuna/work/maia
# DATA=/ceph/users/atuna/work/maia/data
DATA=/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2025_10_08_09h35m49s
NEV=10
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)
STEER=steer_reco_${1}_${2}.py
LOG=log_${NOW}.txt

cp ${CODE}/SteeringMacros/k4Reco/steer_reco.py ${STEER}
sed -i 's|{the_args.data}/sim/{the_args.TypeEvent}/|./|g' ${STEER}
sed -i 's|{the_args.data}/recoBIB/{the_args.TypeEvent}/|./|g' ${STEER}
sed -i 's|_reco_|_digi_|g' ${STEER}
sed -i 's|detector-simulation/geometries|k4geo/MuColl/MAIA/compact|g' ${STEER}
sed -i 's|1666|16|g' ${STEER}

k4run ${STEER} -n ${NEV} --TypeEvent ${1} --InFileName ${2} --enableBIB --skipReco --skipTrackerConing --code ${CODE} --data ${DATA} # | tee ${LOG}
# --enableIP
rm -f lctuple_*.root
