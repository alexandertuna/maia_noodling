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

FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_digi_0.slcio"

INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5

TRACKERS = [
    # "VertexBarrelCollection",
    # "VertexEndcapCollection",
    "InnerTrackerBarrelCollection",
    # "InnerTrackerEndcapCollection",
    "OuterTrackerBarrelCollection",
    # "OuterTrackerEndcapCollection",
]


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default=FNAME,
                        help="Path to the input slcio file")
    parser.add_argument("--pdf", type=str, default="maia_doublet_v0.pdf",
                        help="Path to the output PDF file")
    return parser.parse_args()


def main():

    ops = options()
    fnames = get_inputs(ops.i)

    hits = get_hits(fnames)
    hits = post_process(hits)
    print(hits)

    with PdfPages(ops.pdf) as pdf:
        plot_barrel_xy(hits, pdf)


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
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(fname)
        for event in reader:
            for colname in TRACKERS:
                for hit in event.getCollection(colname):
                    hits.append( [
                        hit.getPositionVec().X(),
                        hit.getPositionVec().Y(),
                        hit.getPositionVec().Z(),
                        hit.getEDep(),
                        hit.getPathLength(),
                        hit.getCellID0(),
                    ] )

    return pd.DataFrame(np.array(hits), columns=["x", "y", "z", "e", "dx", "cellid0"])

def post_process(df: pd.DataFrame) -> pd.DataFrame:
    df["cellid0"] = df["cellid0"].astype(np.int64)
    df["r"] = np.sqrt(df["x"]**2 + df["y"]**2)
    df["system"] = np.right_shift(df["cellid0"], 0) & 0b1_1111
    df["side"] = np.right_shift(df["cellid0"], 5) & 0b11
    df["layer"] = np.right_shift(df["cellid0"], 7) & 0b11_1111
    df["module"] = np.right_shift(df["cellid0"], 13) & 0b111_1111_1111
    df["sensor"] = np.right_shift(df["cellid0"], 24) & 0b1111_1111
    return df

def plot_barrel_xy(df: pd.DataFrame, pdf: PdfPages) -> None:

    colors = {
        INNER_TRACKER_BARREL: [
            "green",
            "purple",
            "green",
            "purple",
            "green",
            "purple",
            "green",
            "purple",
        ],
        OUTER_TRACKER_BARREL: [
            "blue",
            "red",
            "blue",
            "red",
            "blue",
            "red",
            "blue",
            "red",
        ],
    }

    columns = [
        "system",
        "layer",
        "module",
    ]

    for [zoom, xmin, xmax, ymin, ymax] in [
        [False, -1550, 1550, -1550, 1550],
        [True, 480, 580, -50, 50]
    ]:
        fig, ax = plt.subplots(figsize=(8, 8))
        grouped = df.groupby(columns)
        for (system, layer, module), group in grouped:
            x_corners, y_corners = get_points_for_line(group)
            lw = get_line_width(system, zoom)
            ax.plot(x_corners,
                    y_corners,
                    c=colors[system][layer],
                    lw=lw,
                    )

        ax.grid(which="both", linestyle="-", alpha=0.2, c="black", lw=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(top=True, right=True, direction="in")
        ax.set_xlabel("Sim. hit x [mm]")
        ax.set_ylabel("Sim. hit y [mm]")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        if len(TRACKERS) == 1:
            colname = TRACKERS[0]
            ax.set_title(f"{colname} sim. hits")
        fig.subplots_adjust(right=0.98, left=0.16, bottom=0.09, top=0.95)
        pdf.savefig()
        plt.close()


def get_line_width(system: int, zoom: bool) -> float:
    multiplier = 10.0 if zoom else 1.0
    if system == INNER_TRACKER_BARREL:
        return 0.3 * multiplier
    elif system == OUTER_TRACKER_BARREL:
        return 0.7 * multiplier
    else:
        raise Exception(f"Unknown system: {system}")


def get_points_for_line(df: pd.DataFrame) -> tuple[list[float], list[float]]:
    # Assume the points form a rectangle with an angle
    # Find the center of the rectangle (median x and y)
    # Rotate relative to the origin (0, 0) to align with axes
    # Find the min and max x and y in the rotated frame
    # Rotate back to original frame
    x_center = df["x"].median()
    y_center = df["y"].median()
    angle = np.arctan2(y_center, x_center)
    cos_angle = np.cos(-angle)
    sin_angle = np.sin(-angle)
    xp = cos_angle * df["x"] - sin_angle * df["y"]
    yp = sin_angle * df["x"] + cos_angle * df["y"]
    xp_min = xp.min()
    yp_min = yp.min()
    yp_max = yp.max()
    x_corners = []
    y_corners = []
    for xp_c, yp_c in [(xp_min, yp_min),
                       (xp_min, yp_max),
                       ]:
        x_orig = cos_angle * xp_c + sin_angle * yp_c
        y_orig = -sin_angle * xp_c + cos_angle * yp_c
        x_corners.append(x_orig)
        y_corners.append(y_orig)
    return x_corners, y_corners


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
