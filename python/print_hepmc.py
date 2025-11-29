import argparse
import time
import pyhepmc
from pyhepmc.view import savefig

NOW = time.strftime("%Y_%m_%d_%Hh%Mm%Ss")

def arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, help="Input hepmc file")
    parser.add_argument("-n", type=int, help="Number of events to process")
    parser.add_argument("-d", action="store_true", help="Draw events to pdf")
    return parser.parse_args()

def main():

    args = arguments()
    if not args.i:
        raise ValueError("Please provide an input hepmc file with -i")

    with pyhepmc.open(args.i) as f:
        print(f)
        for i, event in enumerate(f):
            if args.d:
                savefig(event, f"hepmc_{NOW}_event{i:04}.pdf")
            print(event)
            if args.n and i >= args.n - 1:
                break


if __name__ == "__main__":
    main()
