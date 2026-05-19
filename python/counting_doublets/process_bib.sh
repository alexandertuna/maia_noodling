GEO="v04"
DIR100=/ceph/users/atuna/work/maia/maia_noodling/samples/${GEO}/neutrinoGun_n5_p15
DIR010=/ceph/users/atuna/work/maia/maia_noodling/samples/${GEO}/neutrinoGun_n5_p15_0.10

for EV in $(seq 0 9); do
# for EV in 2 4 5 6 7 8 9; do

    # INP=${DIR100}/neutrinoGun_digi_${EV}.slcio
    # MCPS=mcps_${EV}.pkl
    # HITS=simhits_${EV}.pkl
    # MDS=mds_${EV}.pkl
    # T2S=t2s_${EV}.pkl
    # time python main.py \
    #      -i ${INP} \
    #      --outer \
    #      --read-mcps ${MCPS} \
    #      --read-simhits ${HITS} \
    #      --read-mds ${MDS} \
    #      --cut-doublets \
    #      --cut-line-segments \
    #      2>&1 | tee log_t2s_${EV}.txt

    INP=${DIR100}/neutrinoGun_digi_${EV}.slcio
    MCPS=mcps_${EV}.pkl
    HITS=simhits_${EV}.pkl
    MDS=mds_${EV}.pkl
    T2S=t2s_${EV}.pkl
    time python main.py \
         -i ${INP} \
         --geo ${GEO} \
         --outer \
         --cut-doublets \
         --cut-line-segments \
         --write-mcps ${MCPS} \
         --write-simhits ${HITS} \
         --write-mds ${MDS} \
         --write-t2s ${T2S} \
         2>&1 | tee log_${GEO}_${EV}.txt


done

