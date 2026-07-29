mkdir -p cards
for IT in $(seq 10000 10999); do
    cp p8_mumu_tt_ecm10000.cmd cards/p8_mumu_tt_ecm10000_${IT}.cmd
    sed -i s/12345/${IT}/g cards/p8_mumu_tt_ecm10000_${IT}.cmd
done
