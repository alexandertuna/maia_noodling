import pyLCIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
plt.rcParams.update({"font.size": 16})

FILE_SIM = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2025_10_17_10h40m00s/BIB10TeV/sim_mm/BIB_sim_1.slcio"
FILE_DIGI = "/ceph/users/atuna/work/maia/maia_noodling/samples/v00/neutrinoGun/neutrinoGun_digi_0.slcio"

COLL_SIM = "InnerTrackerBarrelCollection"
COLL_DIGI = "InnerTrackerBarrelCollection"

SPEED_OF_LIGHT = 299.792458  # mm/ns

def main():
    df_sim = get_dataframe(FILE_SIM, COLL_SIM)
    df_digi = get_dataframe(FILE_DIGI, COLL_DIGI)
    with PdfPages("time_plots.pdf") as pdf:
        plot(df_sim, f"sim hits ({COLL_SIM})", pdf)
        plot(df_digi, f"reco hits ({COLL_DIGI})", pdf)


def get_dataframe(fname: str, collection: str) -> pd.DataFrame:
    print(f"Reading file {fname}, collection {collection} ...")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    rows = []
    for event in reader:
        for hit in event.getCollection(collection):
            row = {
                "hit_x": hit.getPosition()[0],
                "hit_y": hit.getPosition()[1],
                "hit_z": hit.getPosition()[2],
                "hit_time": hit.getTime(),
            }
            rows.append(row)
    df = pd.DataFrame(rows)
    df["hit_R"] = np.sqrt(df["hit_x"]**2 + df["hit_y"]**2 + df["hit_z"]**2)
    df["hit_time_corrected"] = df["hit_time"] - df["hit_R"] / SPEED_OF_LIGHT
    return df


def plot(df: pd.DataFrame, label: str, pdf: PdfPages):
    color = "dodgerblue" if "sim" in label else "orange"
    bins = np.linspace(-5, 15, 401)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.hist(
        df["hit_time_corrected"],
        bins=bins,
        histtype="stepfilled",
        alpha=0.9,
        color=color,
    )
    ax.set_xlabel("Hit time, corrected for propagation (ns)")
    ax.set_ylabel("Counts")
    ax.set_ylim(0.8, None)
    ax.set_title(f"Hit time: {label}")
    ax.minorticks_on()
    ax.grid(which="both")
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
    ax.semilogy()
    pdf.savefig()
    plt.close()


if __name__ == "__main__":
    main()
