CODE=/ceph/users/atuna/work/maia
DATA=/ceph/users/atuna/work/maia/data
ONE="test"
TWO="test_process"
NEV=10
NOW=$(date +%Y_%m_%d_%Hh%Mm%Ss)
LOG=log_${NOW}.txt

cp ${CODE}/SteeringMacros/k4Reco/steer_reco.py steer_reco.py
k4run steer_reco.py -n ${NEV} --TypeEvent ${TWO} --InFileName ${ONE} --enableBIB --enableIP --skipReco --skipTrackerConing --code ${CODE} --data ${DATA} | tee ${LOG}
# --enableIP

mv ${DATA}/recoBIB/test_process/test_process_reco_test.slcio ./test_process_reco_test.slcio__IP_BIB1666
