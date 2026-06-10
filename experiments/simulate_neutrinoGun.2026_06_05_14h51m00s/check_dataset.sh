for GEO in v01 v05; do
    for RES in 0.000 0.005 0.010 0.020; do
        for EV in 0 3; do
            time python ../../python/check_dataset.py -i "${GEO}/${RES}/neutrinoGun_digi_${EV}.slcio" -r --pdf neutrinoGun_${GEO}_${RES}_${EV}.pdf
        done
    done
done
for GEO in v01 v05; do
    for RES in 0.000 0.005 0.010 0.020; do
        time python ../../python/check_dataset.py -i "${GEO}/${RES}/muonGun_pT_2p0_2p1_digi_30*.slcio" --pdf muonGun_${GEO}_${RES}.pdf
    done
done
