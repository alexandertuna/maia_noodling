CODE=/ceph/users/atuna/work/maia

rm -f output_gen.slcio
python ${CODE}/mucoll-benchmarks/generation/pgun/pgun_lcio.py \
    -s 12345 \
    -e 100 \
    --pdg 13 \
    --pdg -13 \
    --p 10 \
    --particles 10 \
    --theta 10 170 \
    -- output_gen.slcio
