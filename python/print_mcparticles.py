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


def get_hits(fnames: list[str]):

    hits = []

    for fname in fnames:

        print(f"Reading {fname} ...")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(fname)
    
        for i_event, event in enumerate(tqdm(reader)):

            # print(i_event, event.getCollectionNames())
            for colname in TRACKERS:

                col = event.getCollection(colname)

                for i_hit, hit in enumerate(col):

                    hits.append( [
                        hit.getPositionVec().X(),
                        hit.getPositionVec().Y(),
                        hit.getPositionVec().Z(),
                        hit.getEDep(),
                    ] )

    return pd.DataFrame(np.array(hits), columns=["x", "y", "z", "e"])




if __name__ == "__main__":
    main()
