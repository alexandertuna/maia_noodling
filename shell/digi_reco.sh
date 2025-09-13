CODE=/ceph/users/atuna/work/maia
DATA=/ceph/users/atuna/work/maia/data
ONE="test"
TWO="test_process"
NEV=20
# mkdir -p ${DATA}/recoBIB/${TWO}
# mkdir -p ${DATA}/IPairs
# mkdir -p ${DATA}/BIB10TeV/sim_mm_pruned
# mkdir -p ${DATA}/BIB10TeV/sim_mp_pruned
# mkdir -p ${DATA}/sim/${TWO}

cp ${CODE}/SteeringMacros/k4Reco/steer_reco.py steer_reco.py
k4run steer_reco.py -n ${NEV} --TypeEvent ${TWO} --InFileName ${ONE} --enableBIB --skipReco --code ${CODE} --data ${DATA}
# --enableIP
