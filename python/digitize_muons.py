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
from pathlib import Path

CODE = "/ceph/users/atuna/work/maia"
COMPACT = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
STEER_SIM = f"{CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py"
STEER_RECO = f"{CODE}/SteeringMacros/k4Reco/steer_reco.py"
STEER_WHIZARD_HBB = f"{CODE}/mucoll-benchmarks/generation/signal/whizard/mumu_H_bb_10TeV.sin"


def arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--gen", action="store_true", help="Generate events")
    parser.add_argument("--sim", action="store_true", help="Simulate events")
    parser.add_argument("--digi", action="store_true", help="Digitize events")
    parser.add_argument("--bib", action="store_true", help="Overlay beam-induced background (BIB) at digitization")
    parser.add_argument("--ip", action="store_true", help="Overlay incoherent pairs (IP) at digitization")
    parser.add_argument("--num", type=int, default=0, help="Job index")
    parser.add_argument("--events", type=int, default=1, help="Number of events")
    parser.add_argument("--typeevent", type=str, default="muonGun_pT_0_10", help="Type of event")
    parser.add_argument("--data", type=str, default="", help="Directory where data files are expected")
    return parser.parse_args()

def main():
    args = arguments()
    if args.gen:
        gen(events=args.events,
            num=args.num,
            typeevent=args.typeevent,
            )
    if args.sim:
        sim(events=args.events,
            num=args.num,
            typeevent=args.typeevent,
            )
    if args.digi:
        if not os.path.isdir(args.data):
            raise ValueError(f"Data directory {args.data} does not exist.")
        digi(events=args.events,
             num=args.num,
             typeevent=args.typeevent,
             data=args.data,
             bib=args.bib,
             ip=args.ip,
             )


def run(cmd):
    print(cmd)
    os.system(cmd)


def gen(events: int, num: int, typeevent: str):
    cmd = gen_command(events, num, typeevent)
    run(cmd)


def sim(events: int, num: int, typeevent: str):
    cmd = sim_command(events, num, typeevent)
    run(cmd)


def digi(events: int, num: int, typeevent: str, data: str, bib: bool, ip: bool):
    steer = f"{typeevent}_steer_digi_{num}.py"
    write_local_digi_steer(steer)
    cmd = digi_command(events=events,
                       num=num,
                       typeevent=typeevent,
                       steer=steer,
                       data=data,
                       bib=bib,
                       ip=ip,
                       )
    run(cmd)


def gen_command(events: int, num: int, typeevent: str):
    if typeevent in ["muonGun_pT_0_10", "muonGun_pT_2p0_2p1"]:
        return gen_command_muongun(events, num, typeevent)
    elif typeevent == "neutrinoGun":
        return gen_command_neutrinogun(events, num, typeevent)
    elif typeevent == "mumu_H_bb_10TeV":
        return gen_command_hbb(events, num, typeevent)
    else:
        raise ValueError(f"Unknown typeevent: {typeevent}")


def gen_command_muongun(events: int, num: int, typeevent: str):
    pdg = "13 -13"
    if typeevent == "muonGun_pT_0_10":
        pt = "0 10"
    elif typeevent == "muonGun_pT_2p0_2p1":
        pt = "2.0 2.1"
    else:
        raise ValueError(f"Unknown muonGun typeevent: {typeevent}")
    particles = "10"
    cmd = f"python {CODE}/mucoll-benchmarks/generation/pgun/pgun_lcio.py \
    -s {num} \
    -e {events} \
    --pdg {pdg} \
    --pt {pt} \
    --particles {particles} \
    --theta 10 170 \
    -- {typeevent}_gen_{num}.slcio"
    return cmd


def gen_command_neutrinogun(events: int, num: int, typeevent: str):
    pdg = "-14" if num % 2 == 0 else "14"
    pt = "0.1"
    particles = "1"
    theta = "90"
    cmd = f"python {CODE}/mucoll-benchmarks/generation/pgun/pgun_lcio.py \
    -s {num} \
    -e {events} \
    --pdg {pdg} \
    --pt {pt} \
    --particles {particles} \
    --theta {theta} \
    -- {typeevent}_gen_{num}.slcio"
    return cmd


def gen_command_hbb(events: int, num: int, typeevent: str):
    local_filename = f"mumu_H_bb_10TeV_{num}.sin"
    write_local_whizard_hbb(local_filename=local_filename,
                            events=events,
                            typeevent=typeevent,
                            num=num)
    rm = remove_whizard_output()
    cmd = f"time whizard {local_filename} && {rm}"
    return cmd


def sim_command(events: int, num: int, typeevent: str):
    suffix = get_suffix(typeevent)
    inp = f"{typeevent}_gen_{num}.{suffix}"
    cmd = f"time ddsim \
        --inputFile {inp} \
        --steeringFile {STEER_SIM} \
        --compactFile {COMPACT} \
        --numberOfEvents {events} \
        --outputFile {typeevent}_sim_{num}.slcio"
    return cmd


def digi_command(events: int, num: int, typeevent: str, steer: str, data: str, bib: bool, ip: bool):
    enable_bib = "--enableBIB" if bib else ""
    enable_ip = "--enableIP" if ip else ""
    cmd = f"time k4run \
        {steer} \
        {enable_bib} \
        {enable_ip} \
        -n {events} \
        --TypeEvent {typeevent} \
        --InFileName {num} \
        --skipReco \
        --skipTrackerConing \
        --code {CODE} \
        --data {data}"
    return cmd


def get_suffix(typeevent: str):
    if typeevent in ["muonGun_pT_0_10",
                     "muonGun_pT_2p0_2p1",
                     "neutrinoGun",
                     ]:
        return "slcio"
    elif typeevent == "mumu_H_bb_10TeV":
        return "hepmc"
    else:
        raise ValueError(f"Unknown typeevent: {typeevent}")


def write_local_digi_steer(local_filename: str):

    # read the original steering file
    steer_path = Path(STEER_RECO)
    steer_text = steer_path.read_text()

    # apply substitutions
    steer_text = steer_text.replace(r"{the_args.data}/sim/{the_args.TypeEvent}/", "./")
    steer_text = steer_text.replace(r"{the_args.data}/reco/{the_args.TypeEvent}/", "./")
    steer_text = steer_text.replace(r"{the_args.data}/recoBIB/{the_args.TypeEvent}/", "./")
    steer_text = steer_text.replace("_reco_", "_digi_")
    steer_text = steer_text.replace("detector-simulation/geometries", "k4geo/MuColl/MAIA/compact")
    # steer_text = steer_text.replace("1666", "16")

    # write the local steering file
    local_path = Path(local_filename)
    local_path.write_text(steer_text)


def write_local_whizard_hbb(local_filename: str, events: int, typeevent: str, num: int):

    # read the original steering file
    steer_path = Path(STEER_WHIZARD_HBB)
    steer_text = steer_path.read_text()

    # apply substitutions
    steer_text = steer_text.replace("seed = 1889", f"seed = {1889 + num}")
    steer_text = steer_text.replace("mumu_H_bb_10TeV", f"{typeevent}_gen_{num}")
    steer_text = steer_text.replace("n_events=100", f"n_events={events}")

    # write the local steering file
    local_path = Path(local_filename)
    local_path.write_text(steer_text)


def remove_whizard_output():
    cmd = "rm -f default* hbb* hdec* opr* whizard.log"
    return cmd


if __name__ == "__main__":
    main()
