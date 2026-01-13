# maia doublet v01 geometry

CODE=/ceph/users/atuna/work/maia
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}
for NUM in {300..499}; do
    time python ${CODE}/maia_noodling/python/digitize_muons.py --gen --sim --num ${NUM} --events 1000 --data $(pwd)
    rm -f lctuple_*
done

# time python ${CODE}/maia_noodling/python/digitize_muons.py --gen --sim --digi --num 0 --events 100 --data $(pwd)
# time python ${CODE}/maia_noodling/python/digitize_muons.py --gen --sim --digi --num 1 --events 100 --data $(pwd)
