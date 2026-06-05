"""
Plot the raw time and speed-of-light-corrected time for sim hits in BIB
"""

from glob import glob
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
    "axes.axisbelow": True,
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

import logging
logger = logging.getLogger(__name__)

import pyLCIO

FLUKA_FILE_PATHS = [
    "/ceph/users/atuna/work/maia/data/FLUKA/summary10*_DET_IP.dat",
    "/ceph/users/atuna/work/maia/data/FLUKA/summary20*_DET_IP.dat",
]
SLCIO_FILE_PATHS = [
    "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2026_01_07_22h00m00s/BIB10TeV/sim_mm_pruned/BIB_sim_10*",
    "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2026_01_07_22h00m00s/BIB10TeV/sim_mp_pruned/BIB_sim_10*",
]
NEUTRINO_FILE_PATHS = [
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15_0.10/neutrinoGun_digi_0.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15_0.10/neutrinoGun_digi_1.slcio",
]
OFFICIAL_FILE_PATHS = [
    # "/ceph/users/atuna/work/maia/data/DataMuC_MAIA_v0/v8/recoBIB/muonGun_pT_0_50/muonGun_pT_0_50_reco_100.slcio",
    "/ceph/users/atuna/work/maia/data/DataMuC_MAIA_v0/v8/special/nuGun_filtered_70_110.slcio",
]

TRACKER_COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
SPEED_OF_LIGHT = 299.792458  # mm/ns
BINS = np.linspace(-10, 30, 401)
WINDOW_LO, WINDOW_HI = [-0.5, 15]


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    fluka_file_paths = parse_filepaths(FLUKA_FILE_PATHS)
    slcio_file_paths = parse_filepaths(SLCIO_FILE_PATHS)
    neutrino_file_paths = parse_filepaths(NEUTRINO_FILE_PATHS)
    official_file_paths = parse_filepaths(OFFICIAL_FILE_PATHS)
    particles = parse_fluka(fluka_file_paths)

    bibsim_hits = parse_slcio(slcio_file_paths)
    neutrino_hits = parse_slcio(neutrino_file_paths)
    official_hits = parse_slcio(official_file_paths)
    with PdfPages("bib_time.pdf") as pdf:
        plot_fluka(particles, pdf)
        plot_slcio(bibsim_hits, pdf, tag="BIB sim")
        plot_slcio(neutrino_hits, pdf, tag="Alex overlay")
        plot_slcio(official_hits, pdf, tag="MAIA overlay")


def plot_fluka(particles: pd.DataFrame, pdf: PdfPages):
    
    fig, ax = plt.subplots()
    ax.hist(
        particles["time"],
        bins=BINS,
        histtype="step",
        edgecolor="black",
        color="red",
        fill=True,
        alpha=0.7,
    )
    ax.set_xlabel("Particle time (ns)")
    ax.set_ylabel("Number of particles")
    ax.set_title("FLUKA particles")
    ax.semilogy()
    pdf.savefig()
    plt.close()


def plot_slcio(hits: pd.DataFrame, pdf: PdfPages, tag: str):
    systems = hits["simhit_system"].unique()
    nickname = {
        3: "Inner Tracker Barrel",
        5: "Outer Tracker Barrel",
    }

    for system in systems:

        df = hits[hits["simhit_system"] == system]
        name = nickname[system]

        # set outline color to be black
        fig, ax = plt.subplots()
        ax.hist(
            df[f"simhit_t"],
            bins=BINS,
            histtype="step",
            edgecolor="black",
            color="dodgerblue",
            fill=True,
            alpha=0.7,
        )
        ax.set_xlabel("Sim hit time (ns)")
        ax.set_ylabel("Number of sim hits")
        ax.set_title(f"{name}, {tag}")
        ax.semilogy()
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots()
        ax.hist(
            df[f"simhit_t_corrected"],
            bins=BINS,
            histtype="step",
            edgecolor="black",
            color="green",
            fill=True,
            alpha=0.7,
        )
        n_window = (
            (df[f"simhit_t_corrected"] > WINDOW_LO) &
            (df[f"simhit_t_corrected"] < WINDOW_HI)
        ).sum()
        f_window = n_window / len(df)
        ax.set_xlabel("Speed-of-light-corrected sim hit time (ns)")
        ax.set_ylabel("Number of sim hits")
        ax.set_title(f"{name}, {tag}")
        ax.text(0.95, 0.95,
                f"f = {f_window:.2f} in [{WINDOW_LO}, {WINDOW_HI}]",
                transform=ax.transAxes,
                va="top",
                ha="right",
                )
        ax.semilogy()
        pdf.savefig()
        plt.close()


def parse_filepaths(
    fnames: str | list[str],
) -> list[str]:
    names = []
    if isinstance(fnames, str):
        fnames = [fnames]
    for fname in fnames:
        names.extend(glob(fname))
    return names


def parse_slcio(slcio_file_paths: list[str]) -> pd.DataFrame:

    rows = []

    n_files = len(slcio_file_paths)

    for i_file, file_path in enumerate(slcio_file_paths):
        logger.info(f"Processing file {i_file + 1}/{n_files}: {file_path} ...")

        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(file_path)

        for event in reader:
            for collection in TRACKER_COLLECTIONS:
                hits = event.getCollection(collection)
                n_hit = len(hits)
                for i_hit, hit in enumerate(hits):
                    if i_hit > 0 and i_hit % 1e6 == 0:
                        logger.info(f"{collection} hit {i_hit}/{n_hit-1} ...")
                    cellid = hit.getCellID0()
                    time = hit.getTime()
                    position = hit.getPosition()
                    correction = (np.sqrt(position[0]**2 + position[1]**2 + position[2]**2) / SPEED_OF_LIGHT)
                    rows.append({
                        'simhit_x': position[0],
                        'simhit_y': position[1],
                        'simhit_z': position[2],
                        'simhit_cellid0': cellid,
                        'simhit_t': time,
                        'simhit_t_corrected': time - correction,
                    })

    logger.info("Merge hits into dataframe ...")
    df = pd.DataFrame(rows)

    logger.info("Post-processing hits ...")
    df["simhit_system"] = np.right_shift(df["simhit_cellid0"], 0) & 0b1_1111
    df["simhit_side"] = np.right_shift(df["simhit_cellid0"], 5) & 0b11
    df["simhit_layer"] = np.right_shift(df["simhit_cellid0"], 7) & 0b11_1111
    df["simhit_module"] = np.right_shift(df["simhit_cellid0"], 13) & 0b111_1111_1111
    df["simhit_sensor"] = np.right_shift(df["simhit_cellid0"], 24) & 0b1111_1111

    return df


def bytes_from_file(filename: str):
    """
    Taken from:
    https://github.com/madbaron/detector-simulation/blob/KITP_10TeV/utils/fluka_remix.py
    """
    line_dt=np.dtype([
        ('fid',  np.int32),
        ('fid_mo',  np.int32),
        ('E', np.float64),
        ('x', np.float64),
        ('y', np.float64),
        ('z', np.float64),
        ('cx', np.float64),
        ('cy', np.float64),
        ('cz', np.float64),
        ('time', np.float64),
        ('x_mu', np.float64),
        ('y_mu', np.float64),
        ('z_mu', np.float64)
    ])
    with open(filename, 'rb') as f:
        while True:
            chunk = np.fromfile(f, dtype=line_dt, count=1)
            if not len(chunk):
                return
            yield chunk


def parse_fluka(fluka_file_paths: list[str]) -> pd.DataFrame:
    """
    Taken from:
    https://github.com/madbaron/detector-simulation/blob/KITP_10TeV/utils/fluka_remix.py
    """
    rows = []
    s_to_ns = 1e9
    n_files = len(fluka_file_paths)

    for i_file, file_in in enumerate(fluka_file_paths):

        logger.info(f"Processing FLUKA file {i_file + 1}/{n_files}: {file_in} ...")

        for iL, data in enumerate(bytes_from_file(file_in)):

            fid,e_kin, x,y,z, cx,cy,cz, time ,z_mu = (data[n][0] for n in [
                'fid', 'E',
                'x', 'y', 'z',
                'cx', 'cy', 'cz', 'time', 'z_mu'
            ])
            time *= s_to_ns

            rows.append({
                'fid': fid,
                'e_kin': e_kin,
                'x': x,
                'y': y,
                'z': z,
                'cx': cx,
                'cy': cy,
                'cz': cz,
                'time': time,
                'z_mu': z_mu,
            })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    main()
