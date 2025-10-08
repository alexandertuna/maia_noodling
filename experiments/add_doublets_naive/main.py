import argparse
import os

GEN = True
SIM = True
EVENTS = 1000
CODE = "/ceph/users/atuna/work/maia"
COMPACT = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", action="store_true", help="Generate events")
    parser.add_argument("--sim", action="store_true", help="Simulate events")
    parser.add_argument("--events", type=int, default=1000, help="Number of events")
    return parser.parse_args()

def main():
    args = args()
    if args.gen:
        gen()
    if args.sim:
        sim()

def run(cmd):
    print(cmd)
    os.system(cmd)

def gen():
    run(gen_command())

def sim():
    run(sim_command())

def gen_command():
    cmd = f"python {CODE}/mucoll-benchmarks/generation/pgun/pgun_lcio.py \
    -s 12345 \
    -e {EVENTS} \
    --pdg 13 \
    --pdg -13 \
    --p 10 \
    --particles 10 \
    --theta 10 170 \
    -- output_gen.slcio"
    return cmd

def sim_command():
    INPUT = "output_gen.slcio"
    STEER = f"{CODE}/SteeringMacros/Sim/sim_steer_GEN_CONDOR.py"

    cmd = f"ddsim \
        --inputFile {INPUT} \
        --steeringFile {STEER} \
        --compactFile {COMPACT} \
        --numberOfEvents {EVENTS} \
        --outputFile output_sim.slcio"
    return cmd

if __name__ == "__main__":
    main()
