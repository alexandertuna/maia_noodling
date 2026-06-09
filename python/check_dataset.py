"""
check_dataset.py - a script to make plots from a slcio file for dataset quality assurance

Run like:
> python check_dataset.py -i my_data.slcio
"""
import pyLCIO

import argparse
from glob import glob
import os
import numpy as np
import pandas as pd
import time
import logging
logger = logging.getLogger(__name__)

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
    "grid.linewidth": 0.5,
    "grid.alpha": 0.1,
    "grid.color": "gray",
    "figure.subplot.left": 0.15,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

INNER_TRACKER_SYSTEM = 3
OUTER_TRACKER_SYSTEM = 5
SIM_COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
DIGI_COLLECTIONS = [
    "IBTrackerHits",
    "OBTrackerHits",
]
DIGI_RELATIONS = [
    "IBTrackerHitsRelations",
    "OBTrackerHitsRelations",
]
NICKNAME = {
    INNER_TRACKER_SYSTEM: "Inner tracker",
    OUTER_TRACKER_SYSTEM: "Outer tracker",
}
COLOR = {
    True: "yellow",
    False: "green",
}
CMAP = {
    True: "gist_rainbow",
    False: "turbo",
}

SPEED_OF_LIGHT = 299.792458  # mm/ns
MM_TO_UM = 1000.0


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    ops = options()
    if not ops.i:
        raise ValueError("Provide input file(s) with -i")
    file_paths = parse_file_paths(ops.i.split(","))

    hits = parse_lcio_files(file_paths)

    with PdfPages(ops.pdf) as pdf:
        plot_hits(hits, pdf)


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", required=True, help="Input slcio file or glob pattern")
    parser.add_argument("--pdf", default="check_dataset.pdf", help="Output pdf file")
    return parser.parse_args()


def parse_file_paths(
        fnames: str | list[str],
    ) -> list[str]:
    names = []
    if isinstance(fnames, str):
        fnames = [fnames]
    for fname in fnames:
        names.extend(glob(fname))
    return names


def parse_lcio_files(file_paths) -> tuple[pd.DataFrame,
                                          pd.DataFrame]:

    hits = []

    for i_fp, file_path in enumerate(file_paths):

        if not os.path.isfile(file_path):
            msg = f"File {file_path} does not exist"
            raise FileNotFoundError(msg)

        # open the SLCIO file
        logger.info(f"Processing file {file_path} ...")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(file_path)

        # event loop
        for i_event, event in enumerate(reader):

            # inspect sim hits
            for collection in SIM_COLLECTIONS:

                col = event.getCollection(collection)
                n_obj = len(col)

                for i_obj, obj in enumerate(col):

                    if i_obj > 0 and i_obj % 1e5 == 0:
                        msg = f"Processing {i_fp}, event {i_event}, {collection}, {i_obj}/{n_obj} ..."
                        logger.info(msg)

                    position = obj.getPosition()
                    sim_position = position
                    time = obj.getTime()
                    correction = np.sqrt(position[0]**2 + position[1]**2 + position[2]**2) / SPEED_OF_LIGHT
                    cellid0 = obj.getCellID0()

                    hits.append({
                        'sim': True,
                        'file': i_fp,
                        'i_event': i_event,
                        'hit_x': position[0],
                        'hit_y': position[1],
                        'hit_z': position[2],
                        'hit_sim_x': sim_position[0],
                        'hit_sim_y': sim_position[1],
                        'hit_sim_z': sim_position[2],
                        'hit_cellid0': cellid0,
                        'hit_t': time,
                        'hit_t_corrected': time - correction,
                    })

            # inspect digi hits
            for collection, relation in zip(DIGI_COLLECTIONS, DIGI_RELATIONS):

                use_relation = relation in event.getCollectionNames()
                col = event.getCollection(relation if use_relation else collection)
                n_obj = len(col)

                for i_obj, obj in enumerate(col):

                    if i_obj > 0 and i_obj % 1e5 == 0:
                        msg = f"Processing {i_fp}, event {i_event}, {collection}, {i_obj}/{n_obj} ..."
                        logger.info(msg)

                    if use_relation:
                        simhit, hit = obj.getTo(), obj.getFrom()
                        sim_position = simhit.getPosition()
                    else:
                        hit = obj
                        sim_position = hit.getPosition()

                    position = hit.getPosition()
                    time = hit.getTime()
                    cellid0 = hit.getCellID0()
                    hits.append({
                        'sim': False,
                        'file': i_fp,
                        'i_event': i_event,
                        'hit_x': position[0],
                        'hit_y': position[1],
                        'hit_z': position[2],
                        'hit_sim_x': sim_position[0],
                        'hit_sim_y': sim_position[1],
                        'hit_sim_z': sim_position[2],
                        'hit_cellid0': cellid0,
                        'hit_t': time,
                        'hit_t_corrected': 0,
                    })

    logger.info(f"Making a dataframe out of {len(hits)} hits ...")
    hits = pd.DataFrame(hits)
    hits = postprocess(hits)

    return hits


def postprocess(df):
    logger.info(f"Decoding cellid ...")
    df["hit_system"] = np.right_shift(df["hit_cellid0"], 0) & 0b1_1111
    df["hit_side"] = np.right_shift(df["hit_cellid0"], 5) & 0b11
    df["hit_layer"] = np.right_shift(df["hit_cellid0"], 7) & 0b11_1111
    df["hit_module"] = np.right_shift(df["hit_cellid0"], 13) & 0b111_1111_1111
    df["hit_sensor"] = np.right_shift(df["hit_cellid0"], 24) & 0b1111_1111
    df["hit_r"] = np.sqrt(df["hit_x"]**2 + df["hit_y"]**2)
    df["hit_dx"] = df["hit_x"] - df["hit_sim_x"]
    df["hit_dy"] = df["hit_y"] - df["hit_sim_y"]
    df["hit_dz"] = df["hit_z"] - df["hit_sim_z"]
    return df


def plot_hits(df, pdf):
    logger.info(f"Plotting hits ... ")
    write_date(pdf)
    for sim in [True, False]:
        hits = df[df['sim'] == sim]
        plot_time(hits, pdf, sim)
        # plot_xy(hits, pdf, sim)
        # plot_xy(hits, pdf, sim, zoom_inner=True)
        # plot_xy(hits, pdf, sim, zoom_outer=True)
        # plot_rz(hits, pdf, sim)
        # plot_rz(hits, pdf, sim, zoom_inner=True)
        # plot_rz(hits, pdf, sim, zoom_outer=True)
        if not sim:
            plot_position_resolution(hits, pdf)


def write_date(pdf: PdfPages):
    logger.info(f"Writing the date and time")
    now = time.strftime("%Y_%m_%d_%Hh%Mm%Ss")
    text = f"Plots made at {now}"
    fig, ax = plt.subplots(figsize=(8, 8))
    args = {"ha":"left", "va":"top", "fontfamily":"monospace"}
    ax.text(0.0, 0.7, text, **args, fontsize=16)
    ax.axis("off")
    pdf.savefig()
    plt.close()


def plot_time(df, pdf, sim):
    logger.info(f"Plotting time ... ")
    bins = np.linspace(-10, 20, 301)

    for (system, hits) in df.groupby(f"hit_system"):

        for corrected in [False, True]:

            if not sim and corrected:
                continue

            col = "hit_t" if not corrected else "hit_t_corrected"

            fig, ax = plt.subplots()
            ax.hist(
                hits[col],
                bins=bins,
                histtype="stepfilled",
                color=COLOR[sim],
                edgecolor="black",
                linewidth=1.0,
                alpha=0.9,
            )
            ax.set_xlabel(col)
            ax.set_ylabel("Hits")
            ax.set_title(f"{NICKNAME[system]}, {'sim' if sim else 'digi'} hits")
            ax.semilogy()
            ax.set_ylim(0.8, None)
            pdf.savefig()
            plt.close()


def plot_xy(df, pdf, sim, zoom_inner=False, zoom_outer=False):
    logger.info(f"Plotting xy ... ")
    if zoom_inner:
        bins = [
            np.linspace(125, 135, 160),
            np.linspace(-30, 30, 200),
        ]
    elif zoom_outer:
        bins = [
            np.linspace(-60, 60, 200),
            np.linspace(815, 830, 160),
        ]    
    else:
        bins = np.linspace(-1500, 1500, 300)
        bins = [bins, bins]

    fig, ax = plt.subplots()
    _, _, _, im = ax.hist2d(
        df["hit_x"],
        df["hit_y"],
        bins=bins,
        cmap=CMAP[sim],
        cmin=0.5,
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Hits")
    ax.set_xlabel("hit_x (mm)")
    ax.set_ylabel("hit_y (mm)")
    ax.set_title(f"{'sim' if sim else 'digi'} hits")
    pdf.savefig()
    plt.close()


def plot_rz(df, pdf, sim, zoom_inner=False, zoom_outer=False):
    logger.info(f"Plotting rz ... ")
    bins = 100
    if zoom_inner:
        bins = [
            np.linspace(-20, 20, 200),
            np.linspace(110, 150, 200),
        ]
    elif zoom_outer:
        bins = [
            np.linspace(-20, 20, 200),
            np.linspace(800, 840, 200),
        ]    
    else:
        bins = [
            np.linspace(-1500, 1500, 150),
            np.linspace(0, 1500, 300),
        ]    

    fig, ax = plt.subplots()
    _, _, _, im = ax.hist2d(
        df["hit_z"],
        df["hit_r"],
        bins=bins,
        cmap=CMAP[sim],
        cmin=0.5,
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Hits")
    ax.set_xlabel("hit_z (mm)")
    ax.set_ylabel("hit_r (mm)")
    ax.set_title(f"{'sim' if sim else 'digi'} hits")
    pdf.savefig()
    plt.close()


def plot_position_resolution(df, pdf):
    logger.info(f"Plotting position resolution ... ")

    q1 = 68.3
    bins = np.linspace(-40, 40, 161)
    subset = df[df["hit_module"] == 0]

    for (system, hits) in subset.groupby(f"hit_system"):
        diff = hits["hit_dy"] * MM_TO_UM
        fig, ax = plt.subplots()
        one_sigma_quantile = np.percentile(np.abs(diff), q1)
        ax.hist(diff, bins=bins)
        ax.set_xlabel("sim y - digi y [um]")
        text = f"{q1}% interval = {one_sigma_quantile:.1f}um"
        ax.set_title(f"{NICKNAME[system]}, phi module=0: {text}", fontsize=15)
        pdf.savefig()
        plt.close()


if __name__ == "__main__":
    main()
