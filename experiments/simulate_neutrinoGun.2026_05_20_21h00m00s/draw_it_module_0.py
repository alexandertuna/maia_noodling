import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection
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
    "figure.subplot.left": 0.16,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

import pyLCIO

FNAME_FALSE = "neutrinoGun_digi_0_ForceHitsOntoSurfaceFalse0.slcio"
FNAME_TRUE = "neutrinoGun_digi_0_ForceHitsOntoSurfaceTrue0.slcio"
COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "IBTrackerHits",
]
RELATIONS = [
    "IBTrackerHitsRelations",
]
EPSILON = 1e-3
MM_TO_UM = 1e3
LAYER_OF_INTEREST = 0
MODULE_OF_INTEREST = 0

def main():
    df_false = get_df(FNAME_FALSE)
    df_true = get_df(FNAME_TRUE)
    df_forced = get_df_forced(FNAME_TRUE)
    with PdfPages("module_0.pdf") as pdf:
        plot(df_false, pdf)
        plot(df_true, pdf)
        plot_forced(df_forced, pdf)

def get_df(fname) -> pd.DataFrame:
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    data = []
    for event in reader:
        for i_col, col_name in enumerate(COLLECTIONS):
            collection = event.getCollection(col_name)
            for hit in collection:
                cellid0 = hit.getCellID0()
                layer, module = (cellid0 >> 7) & 0b11_1111, (cellid0 >> 13) & 0b111_1111_1111
                if layer != LAYER_OF_INTEREST or module != MODULE_OF_INTEREST:
                    continue
                data.append({
                    "hit_collection": i_col,
                    "hit_x": hit.getPosition()[0] * MM_TO_UM,
                    "hit_y": hit.getPosition()[1] * MM_TO_UM,
                    "hit_z": hit.getPosition()[2] * MM_TO_UM,
                    "hit_cellid0": hit.getCellID0(),
                })
    reader.close()

    # merge
    df = pd.DataFrame(data)

    # announce
    for i_col, col_name in enumerate(COLLECTIONS):
        n_hits = len(df[df["hit_collection"] == i_col])
        print(f"Collection: {col_name} ({i_col}) {n_hits} hits")

    # post-process
    df["hit_layer"] = np.right_shift(df["hit_cellid0"], 7) & 0b11_1111
    df["hit_module"] = np.right_shift(df["hit_cellid0"], 13) & 0b111_1111_1111

    # subset to layer=0, module=0
    df = df[(df["hit_layer"] == 0) & (df["hit_module"] == 0)]
    for i_col, col_name in enumerate(COLLECTIONS):
        n_hits = len(df[df["hit_collection"] == i_col])
        print(f"Collection: {col_name} ({i_col}) {n_hits} hits")

    return df


def get_df_forced(fname) -> pd.DataFrame:

    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    data = []
    for event in reader:
        for i_rel, rel_name in enumerate(RELATIONS):
            collection = event.getCollection(rel_name)
            for rel in collection:
                simhit, hit = rel.getTo(), rel.getFrom()
                cellid0 = hit.getCellID0()
                layer, module = (cellid0 >> 7) & 0b11_1111, (cellid0 >> 13) & 0b111_1111_1111
                if layer != LAYER_OF_INTEREST or module != MODULE_OF_INTEREST:
                    continue
                data.append({
                    "hit_collection": i_rel,
                    "hit_x": hit.getPosition()[0] * MM_TO_UM,
                    "hit_y": hit.getPosition()[1] * MM_TO_UM,
                    "hit_z": hit.getPosition()[2] * MM_TO_UM,
                    "hit_cellid0": hit.getCellID0(),
                    "simhit_x": simhit.getPosition()[0] * MM_TO_UM,
                    "simhit_y": simhit.getPosition()[1] * MM_TO_UM,
                    "simhit_z": simhit.getPosition()[2] * MM_TO_UM,
                    "simhit_px": simhit.getMomentum()[0],
                    "simhit_py": simhit.getMomentum()[1],
                    "simhit_pz": simhit.getMomentum()[2],
                })
    reader.close()

    # merge
    df = pd.DataFrame(data)

    # announce
    for i_rel, rel_name in enumerate(RELATIONS):
        n_hits = len(df[df["hit_collection"] == i_rel])
        print(f"Relation: {rel_name} ({i_rel}) {n_hits} hits")

    # post-process
    df["hit_layer"] = np.right_shift(df["hit_cellid0"], 7) & 0b11_1111
    df["hit_module"] = np.right_shift(df["hit_cellid0"], 13) & 0b111_1111_1111

    # subset to layer=0, module=0
    df = df[(df["hit_layer"] == 0) & (df["hit_module"] == 0)]
    for i_rel, rel_name in enumerate(RELATIONS):
        n_hits = len(df[df["hit_collection"] == i_rel])
        print(f"Relation: {rel_name} ({i_rel}) {n_hits} hits")

    return df


def plot(df: pd.DataFrame, pdf: PdfPages):

    ref_x = np.median(np.sort(df[df["hit_collection"] == 1]["hit_x"]))
    ref_y = 0 # np.median(np.sort(df["hit_y"]))
    print(f"Reference x: {ref_x:.4f} mm")
    print(f"Reference y: {ref_y:.4f} mm")

    # scatter plot
    fig, ax = plt.subplots()
    for i_col, col_name in enumerate(COLLECTIONS):
        df_col = df[df["hit_collection"] == i_col]
        ax.scatter(df_col["hit_x"] - ref_x,
                   df_col["hit_y"] - ref_y,
                   s=10,
                   label=col_name)
    ax.set_xlim(-60, 60)
    ax.set_xlabel("Local z (um)")
    ax.set_ylabel("Local y (um)")
    ax.set_title("Hits in layer 0, module 0")
    ax.legend()
    pdf.savefig()
    plt.close()

    # scatter plot of abs(x)
    
    fig, ax = plt.subplots()
    for i_col, col_name in enumerate(COLLECTIONS):
        df_col = df[df["hit_collection"] == i_col]
        ax.scatter(np.abs(df_col["hit_x"] - ref_x) + EPSILON,
                   df_col["hit_y"] - ref_y,
                   s=10,
                   label=col_name)
    ax.set_xlim(EPSILON/2, 100)
    ax.semilogx()
    ax.set_xlabel("Absolute local x (um)")
    ax.set_ylabel("Local y (um)")
    ax.legend()
    pdf.savefig()
    plt.close()

    # normalized histogram of x for i_col=0
    for i_col in range(len(COLLECTIONS)):
        col_name = COLLECTIONS[i_col]
        df_col = df[df["hit_collection"] == i_col]
        weights = np.ones_like(df_col["hit_x"]) / len(df_col)
        bins = np.linspace(-60, 60, 100)
        fig, ax = plt.subplots()
        ax.hist(df_col["hit_x"] - ref_x, bins=bins, weights=weights)
        ax.set_xlabel("Local z (um)")
        ax.set_ylabel("Density")
        ax.set_title(f"{col_name}: {len(df_col)} hits")
        pdf.savefig()
        plt.close()


def plot_forced(df_all: pd.DataFrame, pdf: PdfPages):

    max_rows = 30
    ref_x = 126.9685 * MM_TO_UM # np.median(np.sort(df[df["hit_collection"] == 1]["hit_x"]))
    ref_y = 0 # np.median(np.sort(df["hit_y"]))
    print(f"Reference x: {ref_x:.4f} um")
    print(f"Reference y: {ref_y:.4f} um")

    # scatter plot
    fig, ax = plt.subplots()
    for i_rel, rel_name in enumerate(RELATIONS):

        # subset
        this_col = df_all["hit_collection"] == i_rel
        problem = np.abs(df_all["simhit_x"] - ref_x) > EPSILON
        df = df_all[this_col & problem]

        # get a random sample of max_rows rows
        df = df.sample(n=min(max_rows, len(df)), random_state=42)

        # segments = np.stack([
        #     np.column_stack([df["simhit_x"] - ref_x, df["simhit_y"] - ref_y]),
        #     np.column_stack([df["hit_x"] - ref_x,    df["hit_y"] - ref_y]),
        # ], axis=1)
        # ax.add_collection(LineCollection(segments, colors="gray", linewidths=0.5))

        dx = df["hit_x"] - df["simhit_x"]
        dy = df["hit_y"] - df["simhit_y"]
        ax.quiver(df["simhit_x"] - ref_x,
                  df["simhit_y"] - ref_y,
                  dx,
                  dy,
                  angles="xy", scale_units="xy", scale=1,
                  width=0.002, color="gray")

        ax.scatter(df["hit_x"] - ref_x,
                   df["hit_y"] - ref_y,
                   s=20,
                   color="blue",
                   )
        ax.scatter(df["simhit_x"] - ref_x,
                   df["simhit_y"] - ref_y,
                   s=20,
                   color="black",
                   )
        ax.text(0.05, 0.93, f"Inner Tracker", transform=ax.transAxes, fontsize=20, color="black")
        ax.text(0.05, 0.87, f"Sim hit", transform=ax.transAxes, fontsize=20, color="black")
        ax.text(0.05, 0.81, f"Digi hit", transform=ax.transAxes, fontsize=20, color="blue")

    ax.set_xlim(-60, 60)
    info_x = "Sensor depth = 100um"
    info_y = "Sensor width = 3cm"
    ax.set_xlabel(f"Local z (um). {info_x}")
    ax.set_ylabel(f"Local y (um). {info_y}")
    ax.set_title(f"ForceHitsOntoSurface for {max_rows} out-of-bounds hits")
    pdf.savefig()
    plt.close()



if __name__ == "__main__":
    main()
