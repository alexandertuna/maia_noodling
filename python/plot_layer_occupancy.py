import pyLCIO
import argparse
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({
    "font.size": 16,
    "figure.figsize": (8, 8),
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "axes.grid": True,
    "axes.grid.which": "both",
    # "axes.axisbelow": True,
    "grid.linewidth": 0.5,
    "grid.alpha": 0.1,
    "grid.color": "gray",
    "figure.subplot.left": 0.15,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

TRACKER = "OuterTrackerBarrelCollection"
MUON = 13

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default="output_sim.slcio",
                        help="Path to the input slcio file")
    parser.add_argument("--muons", action="store_true", help="Filter for muon hits only")
    parser.add_argument("--no-muons", action="store_true", help="Exclude muon hits")
    return parser.parse_args()


def main():

    ops = options()
    fnames = sorted(get_inputs(ops.i))
    hits = get_hits(fnames)
    if ops.muons:
        print("Filtering for muon hits only ...")
        hits = hits[np.abs(hits["pdg"]) == MUON]
    elif ops.no_muons:
        print("Excluding muon hits ...")
        hits = hits[np.abs(hits["pdg"]) != MUON]
    with PdfPages("layer_occupancy.pdf") as pdf:
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
    
        for i_event, event in enumerate(reader):

            # if i_event % 1000 == 0:
            #     print(f"Processing event {i_event}")

            col = event.getCollection(TRACKER)
            for hit in col:
                hits.append( [
                    i_event,
                    hit.getPositionVec().X(),
                    hit.getPositionVec().Y(),
                    hit.getPositionVec().Z(),
                    hit.getEDep(),
                    hit.getCellID0(),
                    hit.getMCParticle().getPDG(),
                ] )

    if len(hits) == 0:
        raise Exception("No hits found!")

    print("Making hits dataframe ...")
    columns = ["event", "x", "y", "z", "e", "cellid0", "pdg"]
    dtypes = {
        "event": int,
        "x": float,
        "y": float,
        "z": float,
        "e": float,
        "cellid0": int,
        "pdg": int,
    }
    hits = pd.DataFrame(np.array(hits), columns=columns).astype(dtypes)
    print(hits)

    print("Adding features ...")
    hits["r"] = np.sqrt(hits["x"]**2 + hits["y"]**2)
    hits["system"] = np.right_shift(hits["cellid0"], 0) & 0b1_1111
    hits["side"] = np.right_shift(hits["cellid0"], 5) & 0b11
    hits["layer"] = np.right_shift(hits["cellid0"], 7) & 0b11_1111
    hits["module"] = np.right_shift(hits["cellid0"], 13) & 0b111_1111_1111
    hits["sensor"] = np.right_shift(hits["cellid0"], 24) & 0b1111_1111

    return hits


def make_plots(df: pd.DataFrame, pdf: PdfPages) -> None:

    bins = np.arange(
        df["layer"].min()-0.5,
        df["layer"].max()+1.0,
        1,
    )

    # considering all sensors
    fig, ax = plt.subplots()
    ax.hist(
        df["layer"],
        bins=bins,
        histtype="stepfilled",
        color="yellow",
        edgecolor="black",
        linewidth=1.0,
        alpha=0.9,
    )
    ax.set_xlabel("Layer")
    ax.set_ylabel("Sim. hits")
    ax.set_title(f"{TRACKER} occupancy")
    pdf.savefig()
    plt.close()

    # one plot per sensor
    sensors = sorted(list(df["sensor"].unique()))
    for i_sensor, sensor in enumerate(sensors):
        print(f"Plotting sensor {i_sensor + 1} / {len(sensors)}...")
        fig, ax = plt.subplots()
        mask = df["sensor"] == sensor
        ax.hist(
            df[mask]["layer"],
            bins=bins,
            histtype="stepfilled",
            color="yellow",
            edgecolor="black",
            linewidth=1.0,
            alpha=0.9,
        )
        ax.set_xlabel("Layer")
        ax.set_ylabel("Sim. hits")
        ax.set_title(f"{TRACKER}, sensor {sensor}")
        pdf.savefig()
        plt.close()


if __name__ == "__main__":
    main()
