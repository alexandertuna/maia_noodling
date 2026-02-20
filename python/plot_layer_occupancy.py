import argparse
import glob
import pickle
import numpy as np
import pandas as pd
import warnings
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
import logging
logger = logging.getLogger(__name__)

try:
    import pyLCIO
except ImportError:
    warnings.warn("pyLCIO not found")

PKLNAME = "hits.pkl"


TRACKER = "OuterTrackerBarrelCollection"
ELECTRON = 11
MUON = 13
MUON_NEUTRINO = 14
PHOTON = 22
SPEED_OF_LIGHT = 299.792458  # mm/ns
GEV_TO_KEV = 1e6
EPSILON_ENERGY = 0.1 # keV

INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5
N_MODULES = {
    INNER_TRACKER_BARREL: [15*2, 15*2, 20*2, 20*2, 58*2, 58*2, 62*2, 62*2],
    OUTER_TRACKER_BARREL: [48*2, 48*2, 52*2, 52*2, 80*2, 80*2, 84*2, 84*2],
}

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default="output_sim.slcio",
                        help="Path to the input slcio file")
    parser.add_argument("--edep1kev", action="store_true", help="Filter for hits with energy deposition > 1 keV")
    parser.add_argument("--muons", action="store_true", help="Filter for muon hits only")
    parser.add_argument("--no-muons", action="store_true", help="Exclude muon hits")
    parser.add_argument("--write-to-pkl", action="store_true", help="Write hits to a pickle file")
    parser.add_argument("--read-from-pkl", action="store_true", help="Read hits from a pickle file")
    return parser.parse_args()


def main():

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ops = options()
    fnames = sorted(get_inputs(ops.i))

    if not ops.read_from_pkl:
        hits = get_hits(fnames,
                        only_muons=ops.muons,
                        exclude_muons=ops.no_muons,
                        edep1kev=ops.edep1kev,
                        )
    else:
        logger.info(f"Reading hits from {PKLNAME} ...")
        with open(PKLNAME, "rb") as fi:
            hits = pickle.load(fi)

    if ops.write_to_pkl:
        logger.info(f"Writing hits to {PKLNAME} ...")
        with open(PKLNAME, "wb") as fi:
            pickle.dump(hits, fi)

    # if ops.muons:
    #     logger.info("Filtering for muon hits only ...")
    #     hits = hits[np.abs(hits["pdg"]) == MUON]
    # elif ops.no_muons:
    #     logger.info("Excluding muon hits ...")
    #     hits = hits[np.abs(hits["pdg"]) != MUON]

    with PdfPages("layer_occupancy.pdf") as pdf:
        make_plots(hits, pdf)


def get_inputs(fpath: str) -> list[str]:
    inputs = []
    for fp in fpath.split(","):
        inputs.extend( glob.glob(fp) )
    if len(inputs) == 0:
        raise Exception(f"No input files found: {fpath}")
    return inputs


def get_hits(
    fnames: list[str],
    only_muons: bool = False,
    exclude_muons: bool = False,
    edep1kev: bool = False,
) -> pd.DataFrame:

    if only_muons:
        logger.info("Filtering for muon hits only ...")
    elif exclude_muons:
        logger.info("Excluding muon hits ...")
    if only_muons and exclude_muons:
        raise ValueError("Cannot specify both --muons and --no-muons")

    hits = []

    for i_fname, fname in enumerate(fnames):

        logger.info(f"Reading {fname} ...")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(fname)
    
        for i_event, event in enumerate(reader):

            # if i_event % 1000 == 0:
            #     logger.info(f"Processing event {i_event}")

            col = event.getCollection(TRACKER)
            for i_hit, hit in enumerate(col):

                if only_muons and np.abs(hit.getMCParticle().getPDG()) != MUON:
                    continue
                if exclude_muons and np.abs(hit.getMCParticle().getPDG()) == MUON:
                    continue
                if edep1kev and hit.getEDep() * GEV_TO_KEV < 1.0:
                    continue

                hits.append({
                    "file": i_fname,
                    "event": i_event,
                    "hit": i_hit,
                    "x": hit.getPositionVec().X(),
                    "y": hit.getPositionVec().Y(),
                    "z": hit.getPositionVec().Z(),
                    "t": hit.getTime(),
                    "t_corrected": hit.getTime() - (np.sqrt(hit.getPositionVec().X()**2 + \
                                                            hit.getPositionVec().Y()**2 + \
                                                            hit.getPositionVec().Z()**2) / SPEED_OF_LIGHT),
                    "e": hit.getEDep(),
                    "cellid0": hit.getCellID0(),
                    "pdg": hit.getMCParticle().getPDG(),
                    "vx": hit.getMCParticle().getVertexVec().X(),
                    "vy": hit.getMCParticle().getVertexVec().Y(),
                    "vz": hit.getMCParticle().getVertexVec().Z(),
                })

    if len(hits) == 0:
        raise Exception("No hits found!")

    logger.info("Making hits dataframe ...")
    dtypes = {
        "file": int,
        "event": int,
        "hit": int,
        "x": float,
        "y": float,
        "z": float,
        "t": float,
        "t_corrected": float,
        "e": float,
        "cellid0": int,
        "pdg": int,
        "vx": float,
        "vy": float,
        "vz": float,
    }
    hits = pd.DataFrame(hits).astype(dtypes)
    logger.info(f"\n{hits}")

    logger.info("Adding features ...")
    hits["r"] = np.sqrt(hits["x"]**2 + hits["y"]**2)
    hits["vr"] = np.sqrt(hits["vx"]**2 + hits["vy"]**2)
    hits["system"] = np.right_shift(hits["cellid0"], 0) & 0b1_1111
    hits["side"] = np.right_shift(hits["cellid0"], 5) & 0b11
    hits["layer"] = np.right_shift(hits["cellid0"], 7) & 0b11_1111
    hits["module"] = np.right_shift(hits["cellid0"], 13) & 0b111_1111_1111
    hits["sensor"] = np.right_shift(hits["cellid0"], 24) & 0b1111_1111

    OTL01 = N_MODULES[OUTER_TRACKER_BARREL][0]
    rotation = 2 * np.pi / OTL01
    cos_angle = np.cos(-rotation * hits["module"])
    sin_angle = np.sin(-rotation * hits["module"])
    hits["xp"] = cos_angle * hits["x"] - sin_angle * hits["y"]
    hits["yp"] = sin_angle * hits["x"] + cos_angle * hits["y"]
    hits["vxp"] = cos_angle * hits["vx"] - sin_angle * hits["vy"]
    hits["vyp"] = sin_angle * hits["vx"] + cos_angle * hits["vy"]

    columns = [
        "file",
        "event",
        "layer",
    ]
    hits = hits.sort_values(by=columns).reset_index(drop=True)

    return hits


def make_plots(df: pd.DataFrame, pdf: PdfPages) -> None:

    logger.info("Making plots ...")

    # make plot of layer
    bins = np.arange(
        df["layer"].min()-0.5,
        df["layer"].max()+1.0,
        1,
    )
    # with pd.option_context("display.min_rows", 100,
    #                        "display.max_rows", 100,
    #                        ):
    #     logger.info(f"\n{df}")

    logger.info("Plotting layer ...")
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

    # make plots of vertex coordinates
    mask = (df["system"] == OUTER_TRACKER_BARREL) & df["layer"].isin([0, 1])

    # make plot of energy
    max_kev = df["e"].max() * GEV_TO_KEV
    bins = np.logspace(-1, np.log10(max_kev), 1000)

    logger.info("Plotting energy ...")
    fig, ax = plt.subplots()
    ax.hist(
        df[mask]["e"] * GEV_TO_KEV + EPSILON_ENERGY,
        bins=bins,
        histtype="stepfilled",
        color="yellow",
        edgecolor="black",
        linewidth=1.0,
        alpha=0.9,
    )
    ax.semilogx()
    ax.semilogy()
    ax.set_xlabel("Energy [keV]")
    ax.set_ylabel("Sim. hits")
    ax.set_title(f"{TRACKER}: {mask.sum():.0f} sim. hits")
    pdf.savefig()
    plt.close()

    # position x,y
    logger.info("position x,y ...")
    bins = [
        np.linspace(-1000, 1000, 400),
        np.linspace(-1000, 1000, 400),
    ]
    fig, ax = plt.subplots()
    _, _, _, im = ax.hist2d(
        df[mask]["x"],
        df[mask]["y"],
        bins=bins,
        cmap="gist_rainbow",
        cmin=0.5,
    )
    fig.colorbar(im, ax=ax, label="Sim. hits")
    ax.set_xlabel("Hit position $x$ [mm]")
    ax.set_ylabel("Hit position $y$ [mm]")
    ax.set_title(f"{TRACKER} occupancy")
    pdf.savefig()
    plt.close()

    # position xp,yp
    logger.info("position xp,yp ...")
    bins = [
        np.linspace(-1000, 1000, 400),
        np.linspace(-1000, 1000, 400),
    ]
    fig, ax = plt.subplots()
    _, _, _, im = ax.hist2d(
        df[mask]["xp"],
        df[mask]["yp"],
        bins=bins,
        cmap="gist_rainbow",
        cmin=0.5,
    )
    fig.colorbar(im, ax=ax, label="Sim. hits")
    ax.set_xlabel("Hit position $x_{p}$ [mm]")
    ax.set_ylabel("Hit position $y_{p}$ [mm]")
    ax.set_title(f"{TRACKER} occupancy")
    pdf.savefig()
    plt.close()

    # hit position xp
    for cond in [
        np.ones(len(df), dtype=bool),
        df["layer"] == 0,
        df["layer"] == 1,
    ]:
        logger.info("hit position xp ...")
        bins = np.arange(
            810,
            832,
            0.02,
        )
        fig, ax = plt.subplots()
        ax.hist(
            df[mask & cond]["xp"],
            bins=bins,
            histtype="stepfilled",
            color="lawngreen",
            edgecolor="black",
            linewidth=1.0,
            alpha=0.9,
        )
        ax.set_xlabel("Hit position $x_{p}$ [mm]")
        ax.set_ylabel("Sim. hits")
        ax.set_title(f"{TRACKER} occupancy")
        pdf.savefig()
        plt.close()

    # hit position r
    for cond, desc in [
        (np.ones(len(df), dtype=bool), "all layers"),
        (df["layer"] == 0, "layer 0"),
        (df["layer"] == 1, "layer 1"),
    ]:
        logger.info(f"hit position r ({desc}) ...")
        bins = np.arange(
            810,
            832,
            0.02,
        )
        fig, ax = plt.subplots()
        ax.hist(
            df[mask & cond]["r"],
            bins=bins,
            histtype="stepfilled",
            color="lawngreen",
            edgecolor="black",
            linewidth=1.0,
            alpha=0.9,
        )
        ax.set_xlabel("Hit position $r$ [mm]")
        ax.set_ylabel("Sim. hits")
        ax.set_title(f"{TRACKER} occupancy")
        ax.text(0.15, 0.95, desc, transform=ax.transAxes)
        pdf.savefig()
        plt.close()

    # vertex x,y
    for cond, desc in [
        (np.ones(len(df), dtype=bool), "all layers"),
        (df["layer"] == 0, "layer 0"),
        (df["layer"] == 1, "layer 1"),
    ]:
        logger.info(f"vertex x,y ({desc}) ...")
        bins = [
            np.linspace(-1000, 1000, 200),
            np.linspace(-1000, 1000, 200),
        ]
        fig, ax = plt.subplots()
        _, _, _, im = ax.hist2d(
            df[mask & cond]["vx"],
            df[mask & cond]["vy"],
            bins=bins,
            cmap="gist_rainbow",
            cmin=0.5,
        )
        fig.colorbar(im, ax=ax, label="Sim. hits")
        ax.text(0.15, 0.95, desc, transform=ax.transAxes)
        ax.set_xlabel("Vertex position $x$ [mm]")
        ax.set_ylabel("Vertex position $y$ [mm]")
        ax.set_title(f"{TRACKER} occupancy")
        pdf.savefig()
        plt.close()

    # vertex xp,yp
    logger.info("vertex xp,yp ...")
    bins = [
        np.linspace(-1000, 1000, 200),
        np.linspace(-1000, 1000, 200),
    ]
    fig, ax = plt.subplots()
    _, _, _, im = ax.hist2d(
        df[mask]["vxp"],
        df[mask]["vyp"],
        bins=bins,
        cmap="gist_rainbow",
        cmin=0.5,
    )
    fig.colorbar(im, ax=ax, label="Sim. hits")
    ax.set_xlabel("Vertex position $x_{p}$ [mm]")
    ax.set_ylabel("Vertex position $y_{p}$ [mm]")
    ax.set_title(f"{TRACKER} occupancy")
    pdf.savefig()
    plt.close()

    # vertex xp
    logger.info("vertex xp ...")
    hitl0 = df["layer"] == 0
    hitl1 = df["layer"] == 1
    vertexl0 = ((df["vxp"] > 818) & (df["vxp"] < 820)) | ((df["vxp"] > 822) & (df["vxp"] < 824))
    vertexl1 = ((df["vxp"] > 820) & (df["vxp"] < 822)) | ((df["vxp"] > 824) & (df["vxp"] < 826))
    for cond, desc in [
        (np.ones(len(df), dtype=bool), "all layers"),
        (hitl0, "hit in layer 0"),
        (hitl1, "hit in layer 1"),
        (vertexl0, "vertex in layer 0"),
        (vertexl1, "vertex in layer 1"),
        (hitl0 & vertexl0, "vertex in layer 0 and hit in layer 0"),
        (hitl1 & vertexl1, "vertex in layer 1 and hit in layer 1"),
        (hitl0 & vertexl1, "vertex in layer 1 and hit in layer 0"),
        (hitl1 & vertexl0, "vertex in layer 0 and hit in layer 1"),
    ]:
        logger.info(f"vertex xp ({desc}) ...")
        bins = np.arange(
            810,
            832,
            0.1,
        )
        fig, ax = plt.subplots()
        counts, _, _ = ax.hist(
            df[mask & cond]["vxp"],
            bins=bins,
            histtype="stepfilled",
            color="lawngreen",
            edgecolor="black",
            linewidth=1.0,
            alpha=0.9,
        )
        counts = np.sum(counts)
        ax.text(0.15, 0.95, desc, transform=ax.transAxes)
        ax.set_xlabel("Vertex position $x_{p}$ [mm]")
        ax.set_ylabel("Sim. hits")
        ax.set_title(f"{TRACKER}: {counts:.0f} sim. hits")
        pdf.savefig()
        plt.close()

    # vertex r
    logger.info("vertex r ...")
    hitl0 = df["layer"] == 0
    hitl1 = df["layer"] == 1
    vertexl0 = ((df["vxp"] > 818) & (df["vxp"] < 820)) | ((df["vxp"] > 822) & (df["vxp"] < 824))
    vertexl1 = ((df["vxp"] > 820) & (df["vxp"] < 822)) | ((df["vxp"] > 824) & (df["vxp"] < 826))
    for cond, desc in [
        (np.ones(len(df), dtype=bool), "all layers"),
        (hitl0, "hit in layer 0"),
        (hitl1, "hit in layer 1"),
        (vertexl0, "vertex in layer 0"),
        (vertexl1, "vertex in layer 1"),
        (hitl0 & vertexl0, "vertex in layer 0 and hit in layer 0"),
        (hitl1 & vertexl1, "vertex in layer 1 and hit in layer 1"),
        (hitl0 & vertexl1, "vertex in layer 1 and hit in layer 0"),
        (hitl1 & vertexl0, "vertex in layer 0 and hit in layer 1"),
    ]:
        logger.info(f"vertex r ({desc}) ...")
        bins = np.arange(
            810,
            832,
            0.1,
        )
        fig, ax = plt.subplots()
        counts, _, _ = ax.hist(
            df[mask & cond]["vr"],
            bins=bins,
            histtype="stepfilled",
            color="lawngreen",
            edgecolor="black",
            linewidth=1.0,
            alpha=0.9,
        )
        counts = np.sum(counts)
        ax.text(0.15, 0.95, desc, transform=ax.transAxes)
        ax.set_xlabel("Vertex position $r$ [mm]")
        ax.set_ylabel("Sim. hits")
        ax.set_title(f"{TRACKER}: {counts:.0f} sim. hits")
        pdf.savefig()
        plt.close()

    # vertex x
    logger.info("vertex x ...")
    mask = (df["module"] == 0) & (df["system"] == OUTER_TRACKER_BARREL) & df["layer"].isin([0, 1]) 
    bins = np.arange(
        810,
        832,
        0.02,
    )
    fig, ax = plt.subplots()
    ax.hist(
        df[mask]["vx"],
        bins=bins,
        histtype="stepfilled",
        color="lawngreen",
        edgecolor="black",
        linewidth=1.0,
        alpha=0.9,
    )
    ax.set_xlabel("Vertex position $x$ [mm]")
    ax.set_ylabel("Sim. hits")
    ax.set_title(f"{TRACKER} occupancy")
    pdf.savefig()
    plt.close()


if __name__ == "__main__":
    main()
