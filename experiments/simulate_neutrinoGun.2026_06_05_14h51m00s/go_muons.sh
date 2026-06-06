MAX_JOBS=10
CODE=/ceph/users/atuna/work/maia
# RESOLUTIONUV="0.010"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
# source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

for RESOLUTIONUV in 0.000 0.005 0.010 0.020; do

    mkdir -p ${RESOLUTIONUV}

    for NUM in {310..349}; do

        time python digitize_muons.py\
             --gen \
             --sim \
             --digi \
             --num ${NUM} \
             --typeevent muonGun_pT_2p0_2p1 \
             --events 1000 \
             --ResolutionUV ${RESOLUTIONUV} \
             --data $(pwd) # &> log_${NUM}.txt &

        mv muonGun_pT_2p0_2p1_* ${RESOLUTIONUV}/

    done

done

echo "Waiting!"
wait
echo "Done ^.^"
