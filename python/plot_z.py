import pyLCIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
plt.rcParams.update({"font.size": 16})

COLL = "OuterTrackerBarrelCollection"
FILE_0 = "/ceph/users/atuna/work/maia/maia_noodling/samples/v00/neutrinoGun/neutrinoGun_digi_3.slcio"
FILE_1 = "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun/neutrinoGun_digi_3.slcio"
LAYERS = list(range(8))


def main():
    df_0 = get_dataframe(FILE_0, COLL)
    df_1 = get_dataframe(FILE_1, COLL)
    with PdfPages("z_plots.pdf") as pdf:
        plot(df_0, f"Geo v0, {COLL}", LAYERS, pdf)
        plot(df_1, f"Geo v1, {COLL}", LAYERS, pdf)
        for layer in LAYERS:
            plot(df_1, f"Geo v1, {COLL}, layer {layer}", [layer], pdf)


def get_dataframe(fname: str, collection: str) -> pd.DataFrame:
    print(f"Reading file {fname}, collection {collection} ...")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    rows = []
    for event in reader:
        n_hit = len(event.getCollection(collection))
        for i_hit, hit in enumerate(event.getCollection(collection)):
            if i_hit % 1e6 == 0:
                print(f"  Processing hit {i_hit} / {n_hit} ...")
            row = {
                "hit_x": hit.getPosition()[0],
                "hit_y": hit.getPosition()[1],
                "hit_z": hit.getPosition()[2],
                "hit_layer": (hit.getCellID0() >> 7) & 0b11_1111,
            }
            rows.append(row)
    df = pd.DataFrame(rows)
    return df


def plot(df: pd.DataFrame, label: str, layers: list[int], pdf: PdfPages):
    print(f"Plotting {label} for layers {layers} ...")
    color = "dodgerblue" if "v0" in label else "green"
    inner = COLL == "InnerTrackerBarrelCollection"
    bins = np.linspace(-700, 700, 351) if inner else np.linspace(-1300, 1300, 261)
    mask = np.isin(df["hit_layer"], layers)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.hist(
        df["hit_z"][mask],
        bins=bins,
        histtype="stepfilled",
        edgecolor="black",
        linewidth=1.0,
        alpha=0.9,
        color=color,
    )
    ax.set_xlabel("Hit z position (mm)")
    ax.set_ylabel("Counts")
    ax.set_ylim(0, 81e3 if inner else 36e3)
    ax.set_title(f"{label}, event 0")
    ax.minorticks_on()
    ax.grid(which="both")
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.16, right=0.95, top=0.95, bottom=0.09)
    # ax.semilogy()
    pdf.savefig()
    plt.close()


if __name__ == "__main__":
    main()
