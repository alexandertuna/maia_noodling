import pyLCIO
import argparse
import os
import glob
import numpy as np

MCPARTICLE = "MCParticle"

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, required=True,
                        help="Path to the input slcio file")
    return parser.parse_args()


def main():

    ops = options()
    fnames = get_inputs(ops.i)

    for fname in fnames:
        print_mcparticles(fname)


def get_inputs(fpath: str) -> list[str]:
    inputs = []
    for fp in fpath.split(","):
        inputs.extend( glob.glob(fp) )
    if len(inputs) == 0:
        raise Exception(f"No input files found: {fpath}")
    return inputs


def print_mcparticles(fname: str):

    print(f"Reading {fname} ...")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)

    for i_event, event in enumerate(reader):

        col = event.getCollection(MCPARTICLE)
        n_mc = col.getNumberOfElements()
        print(f"{fname=} {i_event=} {n_mc=}")
        for i_part, part in enumerate(col):
            pdgid, energy, mom = part.getPDG(), part.getEnergy(), part.getMomentum()
            px, py, pz = mom[0], mom[1], mom[2]
            pt = np.sqrt(px**2 + py**2)
            print(f"{i_event=} {i_part=} {pdgid=} {energy=:7.3f} {px=:7.3f} {py=:7.3f} {pz=:7.3f} {pt=:7.3f}")


if __name__ == "__main__":
    main()
