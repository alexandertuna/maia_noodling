MAX_JOBS=10
CODE=/ceph/users/atuna/work/maia
TYPEEVENT="muonGun_pT_0_10"
# RESOLUTIONUV="0.010"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
# source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
# export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

for RESOLUTIONUV in 0.000 0.005 0.010 0.020; do

    mkdir -p v05/${RESOLUTIONUV}

    for NUM in {310..399}; do

        while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
            echo "Waiting at $(date) ..."
            sleep 10s
        done

        time python digitize_muons_v05.py \
             --gen \
             --sim \
             --digi \
             --num ${NUM} \
             --typeevent ${TYPEEVENT} \
             --events 1000 \
             --ResolutionUV ${RESOLUTIONUV} \
             --data $(pwd) &> ${TYPEEVENT}_log_${NUM}.txt &

    done

    echo "Waiting!"
    wait
    mv ${TYPEEVENT}_* v05/${RESOLUTIONUV}/

done

echo "Done ^.^"
