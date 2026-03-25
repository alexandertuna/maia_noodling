CODE=/ceph/users/atuna/work/maia
BIBDATA=/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2025_10_17_10h40m00s

# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}
time python ${CODE}/maia_noodling/python/digitize_muons.py --num 0 --events 1 --data ${BIBDATA} --typeevent neutrinoGun --bib --digi # --gen --sim --digi
# time python ${CODE}/maia_noodling/python/digitize_muons.py --num 0 --events 1 --data ${DATA} --typeevent muonGun_pT_0_10 --bib --gen --sim --digi
rm -f lctuple_*

# time python ${CODE}/maia_noodling/python/digitize_muons.py --gen --sim --digi --num 0 --events 100 --data $(pwd)
# time python ${CODE}/maia_noodling/python/digitize_muons.py --gen --sim --digi --num 1 --events 100 --data $(pwd)
