# maia doublet geometry: everything disabled except OT L0, L1
# Im trying to figure out why L1 has more hits than L0

CODE=/ceph/users/atuna/work/maia
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}
for NUM in {102..104}; do
    time python digitize_muons.py --gen --sim --num ${NUM} --events 10000 --data $(pwd)
    rm -f lctuple_*
done

