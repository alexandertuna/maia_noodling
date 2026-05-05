for HUNNY in $(seq 0 9); do
    TAG=ttbar_reco_merge_${HUNNY}XX
    time lcio_merge_files ${TAG}.slcio ttbar_reco_${HUNNY}*.slcio
    time lcio2edm4hep ${TAG}.slcio ${TAG}_edm4hep.root
done
