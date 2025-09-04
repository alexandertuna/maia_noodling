rm -f output_gen.slcio
python ../mucoll-benchmarks/generation/pgun/pgun_lcio.py \
    -s 12345 \
    -e 1000 \
    --pdg 13 \
    --pdg -13 \
    --p 10 \
    --particles 10 \
    --theta 10 170 \
    -- output_gen.slcio
