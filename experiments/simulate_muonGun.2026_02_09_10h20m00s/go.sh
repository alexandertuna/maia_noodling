# maia doublet geometry: everything disabled except IT L0, L1, L2
# Im trying to figure out why insideBounds is false sometimes

CODE=/ceph/users/atuna/work/maia
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}
for NUM in {100..100}; do
    time python digitize_muons.py --gen --sim --num ${NUM} --events 10000 --data $(pwd)
    rm -f lctuple_*
done

