CODE=/ceph/users/atuna/work/maia
EVENTS=1
SEED=${1:-12345}
# use command-line arg or default to 12345

rm -f output_gen.slcio
python ${CODE}/mucoll-benchmarks/generation/pgun/pgun_lcio.py \
    -s ${SEED} \
    -e ${EVENTS} \
    --pdg 13 \
    --pdg -13 \
    --pt 0 10 \
    --particles 10 \
    --theta 10 170 \
    -- output_gen.slcio
