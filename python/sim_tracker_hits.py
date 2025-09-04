import pyLCIO
import argparse
import os
import glob
from tqdm import tqdm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({'font.size': 16})


TRACKERS = [
    "VertexBarrelCollection",
    # "VertexEndcapCollection",
    # "InnerTrackerBarrelCollection",
    # "InnerTrackerEndcapCollection",
    # "OuterTrackerBarrelCollection",
    # "OuterTrackerEndcapCollection",
]


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default="/ceph/users/atuna/work/maia/run/output_sim.slcio",
                        help="Path to the input slcio file")
    return parser.parse_args()


def main():

    ops = options()
    fnames = get_inputs(ops.i)

    hits = get_hits(fnames)
    hits["r"] = np.sqrt(hits["x"]**2 + hits["y"]**2)
    print(hits.head())

    with PdfPages("output_sim.pdf") as pdf:
        make_plots(hits, pdf)


def get_inputs(fpath: str) -> list[str]:
    inputs = []
    for fp in fpath.split(","):
        inputs.extend( glob.glob(fp) )
    if len(inputs) == 0:
        raise Exception(f"No input files found: {fpath}")
    return inputs


def get_hits(fnames: list[str]) -> pd.DataFrame:

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


def make_plots(df: pd.DataFrame, pdf: PdfPages) -> None:
    rmax = df["r"].max() * 1.1

    # xy plot
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df["x"], df["y"], color=get_color(), s=1)
    ax.tick_params(top=True, right=True, direction="in")
    ax.set_xlabel("Sim. hit x [mm]")
    ax.set_ylabel("Sim. hit y [mm]")
    ax.set_xlim(-rmax, rmax)
    ax.set_ylim(-rmax, rmax)
    if len(TRACKERS) == 1:
        colname = TRACKERS[0]
        ax.set_title(f"{colname} sim. hits")
    fig.subplots_adjust(right=0.98, left=0.16, bottom=0.09, top=0.95)
    pdf.savefig()
    plt.close()

def get_color() -> str:
    if len(TRACKERS) == 1:
        tr = TRACKERS[0]
        if "Vertex" in tr:
            return "blue"
        elif "Inner" in tr:
            return "red"
        elif "Outer" in tr:
            return "green"
        raise Exception(f"What? {tr}")
    return "black"


if __name__ == "__main__":
    main()
