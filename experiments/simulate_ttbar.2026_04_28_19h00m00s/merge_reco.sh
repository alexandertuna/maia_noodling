# sequential version
# for HUNNY in $(seq 0 0); do
#     TAG=ttbar_reco_merge_${HUNNY}XX
#     echo "Working on ${TAG} sequentially ... "
#     time lcio_merge_files ${TAG}.slcio ttbar_reco_${HUNNY}*.slcio
#     time lcio2edm4hep ${TAG}.slcio ${TAG}_edm4hep.root
# done

# parallel version
for HUNNY in $(seq 0 9); do
    echo "Working on ${HUNNY} ... "
    hadd ttbar_reco_merge_${HUNNY}XX_edm4hep.root ttbar_reco_${HUNNY}*_edm4hep.root &
    sleep 1
    # (
    #     TAG=ttbar_reco_merge_${HUNNY}XX
    #     echo "Working on ${TAG} in parallel ... "
    #     time lcio_merge_files ${TAG}.slcio ttbar_reco_${HUNNY}*.slcio
    #     time lcio2edm4hep ${TAG}.slcio ${TAG}_edm4hep.root
    # ) > log_${HUNNY}.txt 2>&1 &
done
wait
echo "All done"
