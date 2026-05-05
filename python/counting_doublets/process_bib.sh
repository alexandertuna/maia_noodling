DIR100=/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15
DIR010=/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15_0.10

for EV in $(seq 0 9); do
    INP=${DIR100}/neutrinoGun_digi_${EV}.slcio
    MCPS=mcps_${EV}.pkl
    HITS=simhits_${EV}.pkl
    MDS=mds_${EV}.pkl
    time python main.py -i ${INP} --outer --write-mcps ${MCPS} --write-simhits ${HITS} --write-mds ${MDS} --cut-doublets 2>&1 | tee log_${EV}.txt
done

