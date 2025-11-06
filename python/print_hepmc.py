import argparse
import pyhepmc

# FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_hbb.2025_10_23_16h35m00s/mumu_H_bb_10TeV.hepmc"

def arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, help="Input hepmc file")
    parser.add_argument("-n", type=int, help="Number of events to process")
    return parser.parse_args()

def main():

    args = arguments()
    if not args.i:
        raise ValueError("Please provide an input hepmc file with -i")

    with pyhepmc.open(args.i) as f:
        for i, event in enumerate(f):
            print(event)
            if args.n and i >= args.n - 1:
                break


if __name__ == "__main__":
    main()
