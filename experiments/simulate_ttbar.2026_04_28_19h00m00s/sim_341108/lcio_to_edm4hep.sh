MAX_JOBS=20

for EV in $(seq -w 0 999); do

    while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
        echo "Waiting at $(date) ..."
        sleep 1
    done

    echo "Processing ${EV}"
    lcio2edm4hep ttbar_reco_${EV}.slcio ttbar_reco_${EV}_edm4hep.root &

done
echo "Waiting for stragglers ... "
wait


# lcio2edm4hep ttbar_reco_050.slcio zz_ttbar_reco_050.root
# lcio2edm4hep ttbar_reco_051.slcio zz_ttbar_reco_051.root
# lcio2edm4hep ttbar_reco_052.slcio zz_ttbar_reco_052.root
# lcio2edm4hep ttbar_reco_053.slcio zz_ttbar_reco_053.root
# lcio2edm4hep ttbar_reco_054.slcio zz_ttbar_reco_054.root
# lcio2edm4hep ttbar_reco_055.slcio zz_ttbar_reco_055.root
# lcio2edm4hep ttbar_reco_056.slcio zz_ttbar_reco_056.root
# lcio2edm4hep ttbar_reco_057.slcio zz_ttbar_reco_057.root
# lcio2edm4hep ttbar_reco_058.slcio zz_ttbar_reco_058.root
# lcio2edm4hep ttbar_reco_059.slcio zz_ttbar_reco_059.root
# lcio2edm4hep ttbar_reco_060.slcio zz_ttbar_reco_060.root
# lcio2edm4hep ttbar_reco_061.slcio zz_ttbar_reco_061.root
# lcio2edm4hep ttbar_reco_062.slcio zz_ttbar_reco_062.root
# lcio2edm4hep ttbar_reco_063.slcio zz_ttbar_reco_063.root
# lcio2edm4hep ttbar_reco_064.slcio zz_ttbar_reco_064.root
# lcio2edm4hep ttbar_reco_065.slcio zz_ttbar_reco_065.root
# lcio2edm4hep ttbar_reco_066.slcio zz_ttbar_reco_066.root
# lcio2edm4hep ttbar_reco_067.slcio zz_ttbar_reco_067.root
# lcio2edm4hep ttbar_reco_068.slcio zz_ttbar_reco_068.root
# lcio2edm4hep ttbar_reco_069.slcio zz_ttbar_reco_069.root
