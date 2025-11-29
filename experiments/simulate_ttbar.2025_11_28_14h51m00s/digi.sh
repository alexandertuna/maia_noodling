CODE=/ceph/users/atuna/work/maia
NEV=1
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)
STEER=steer_reco_${1}_${2}.py
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

cp ${CODE}/SteeringMacros/k4Reco/steer_reco.py ${STEER}
sed -i 's|{the_args.data}/sim/{the_args.TypeEvent}/|./|g' ${STEER}
sed -i 's|{the_args.data}/reco/{the_args.TypeEvent}/|./|g' ${STEER}
sed -i 's|{the_args.data}/recoBIB/{the_args.TypeEvent}/|./|g' ${STEER}
# sed -i 's|_reco_|_digi_|g' ${STEER}

time k4run ${STEER} -n ${NEV} --TypeEvent ${1} --InFileName ${2} --code ${CODE} # --skipReco --skipTrackerConing
rm -f lctuple_*.root
