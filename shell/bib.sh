NUM=1
NORM=45
SUMMARY=/ceph/users/atuna/work/maia/data/FLUKA/summary${NUM}_DET_IP.dat
SUMMARY_0=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+0))_DET_IP.dat
SUMMARY_1=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+1))_DET_IP.dat
SUMMARY_2=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+2))_DET_IP.dat
SUMMARY_3=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+3))_DET_IP.dat
SUMMARY_4=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+4))_DET_IP.dat
SUMMARY_5=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+5))_DET_IP.dat
SUMMARY_6=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+6))_DET_IP.dat
SUMMARY_7=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+7))_DET_IP.dat
SUMMARY_8=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+8))_DET_IP.dat
SUMMARY_9=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+9))_DET_IP.dat
SUMMARY_10=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+10))_DET_IP.dat
SUMMARY_11=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+11))_DET_IP.dat
SUMMARY_12=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+12))_DET_IP.dat
SUMMARY_13=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+13))_DET_IP.dat
SUMMARY_14=/ceph/users/atuna/work/maia/data/FLUKA/summary$((NUM+14))_DET_IP.dat
COMPACT=/ceph/users/atuna/work/maia/detector-simulation/geometries/MAIA_v0/MAIA_v0.xml

rm -f BIBinput.slcio
python3 ../../detector-simulation/utils/fluka_to_slcio_new.py \
        -n ${NORM} \
        ${SUMMARY_0} \
        ${SUMMARY_1} \
        ${SUMMARY_2} \
        ${SUMMARY_3} \
        ${SUMMARY_4} \
        ${SUMMARY_5} \
        ${SUMMARY_6} \
        ${SUMMARY_7} \
        ${SUMMARY_8} \
        ${SUMMARY_9} \
        ${SUMMARY_10} \
        ${SUMMARY_11} \
        ${SUMMARY_12} \
        ${SUMMARY_13} \
        ${SUMMARY_14} \
        BIBinput.slcio

cp ../../SteeringMacros/Sim/sim_steer_BIB_CONDOR.py sim_EVENT_${NUM}.py
sed -i 's/OUTFILENAME/"BIB_sim.slcio"/g' sim_EVENT_${NUM}.py

ddsim --steeringFile sim_EVENT_${NUM}.py --inputFiles BIBinput.slcio --compactFile ${COMPACT}
