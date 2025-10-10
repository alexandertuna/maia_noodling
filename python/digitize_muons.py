"""
Convert a shell script into python:

# constants
CODE=/ceph/users/atuna/work/maia
TYPEEVENT="muonGun_pT_0_10"
NUM=${1}
echo "CODE=${CODE}"
echo "TYPEEVENT=${TYPEEVENT}"
echo "NUM=${NUM}"

# env
# it would be cool if setup_mucoll existed out-of-the-box
# setup_mucoll
source /opt/spack/opt/spack/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/__spack_path_placeholder__/linux-x86_64/mucoll-stack-master-2wtmg3ohr26uckseodhqjfjaw7mijwil/setup.sh
export MARLIN_DLL=$(readlink -e ${CODE}/MyBIBUtils/build/lib/libMyBIBUtils.so):${MARLIN_DLL}

# run
time source ${CODE}/maia_noodling/shell/gen.sh ${NUM}
time source ${CODE}/maia_noodling/shell/sim.sh
mv output_sim.slcio ${TYPEEVENT}_sim_${NUM}.slcio
time source ${CODE}/maia_noodling/shell/digi.sh ${TYPEEVENT} ${NUM}
rm -f output_gen.slcio
"""

import argparse
import os
import re
from pathlib import Path

CODE = "/ceph/users/atuna/work/maia"
COMPACT = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
STEER_SIM = f"{CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py"
STEER_RECO = f"{CODE}/SteeringMacros/k4Reco/steer_reco.py"


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", action="store_true", help="Generate events")
    parser.add_argument("--sim", action="store_true", help="Simulate events")
    parser.add_argument("--digi", action="store_true", help="Digitize events")
    parser.add_argument("--num", type=int, default=0, help="Job index")
    parser.add_argument("--events", type=int, default=1, help="Number of events")
    parser.add_argument("--typeevent", type=str, default="muonGun_pT_0_10", help="Type of event")
    parser.add_argument("--data", type=str, default="", help="Directory where data files are expected")
    return parser.parse_args()

def main():
    args = arguments()
    if args.gen:
        gen(args.events,
            args.num,
            args.typeevent,
            )
    if args.sim:
        sim(args.events,
            args.num,
            args.typeevent,
            )
    if args.digi:
        if not os.path.isdir(args.data):
            raise ValueError(f"Data directory {args.data} does not exist.")
        digi(args.events,
             args.num,
             args.typeevent,
             args.data
             )


def run(cmd):
    print(cmd)
    os.system(cmd)


def gen(events: int, num: int, typeevent: str):
    run(gen_command(events, num, typeevent))


def sim(events: int, num: int, typeevent: str):
    run(sim_command(events, num, typeevent))


def digi(events: int, num: int, typeevent: str, data: str):
    steer = f"{typeevent}_steer_digi_{num}.py"
    write_local_digi_steer(steer)
    run(digi_command(events, num, typeevent, steer, data))


def gen_command(events: int, num: int, typeevent: str):
    cmd = f"python {CODE}/mucoll-benchmarks/generation/pgun/pgun_lcio.py \
    -s {num} \
    -e {events} \
    --pdg 13 \
    --pdg -13 \
    --pt 0 10 \
    --particles 10 \
    --theta 10 170 \
    -- {typeevent}_gen_{num}.slcio"
    return cmd


def sim_command(events: int, num: int, typeevent: str):
    inp = f"{typeevent}_gen_{num}.slcio"
    cmd = f"ddsim \
        --inputFile {inp} \
        --steeringFile {STEER_SIM} \
        --compactFile {COMPACT} \
        --numberOfEvents {events} \
        --outputFile {typeevent}_sim_{num}.slcio"
    return cmd


def digi_command(events: int, num: int, typeevent: str, steer: str, data: str):
    cmd = f"k4run \
        {steer} \
        -n {events} \
        --TypeEvent {typeevent} \
        --InFileName {num} \
        --enableBIB \
        --skipReco \
        --skipTrackerConing \
        --code {CODE} \
        --data {data}"
    return cmd


def write_local_digi_steer(local_filename: str):

    # read the original steering file
    steer_path = Path(STEER_RECO)
    steer_text = steer_path.read_text()

    # apply substitutions
    steer_text = steer_text.replace(r"{the_args.data}/sim/{the_args.TypeEvent}/", "./")
    steer_text = steer_text.replace(r"{the_args.data}/recoBIB/{the_args.TypeEvent}/", "./")
    steer_text = steer_text.replace("_reco_", "_digi_")
    steer_text = steer_text.replace("detector-simulation/geometries", "k4geo/MuColl/MAIA/compact")
    steer_text = steer_text.replace("1666", "16")

    # write the local steering file
    local_path = Path(local_filename)
    local_path.write_text(steer_text)


if __name__ == "__main__":
    main()
