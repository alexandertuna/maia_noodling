import pyLCIO
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


SIM_NAME = "muonGun_pT_2p0_2p1_sim_300.slcio"
DIGI_NAMES = [
    "muonGun_pT_2p0_2p1_digi_300.slcio",
    "muonGun_pT_2p0_2p1_digi_301.slcio",
    "muonGun_pT_2p0_2p1_digi_302.slcio",
    "muonGun_pT_2p0_2p1_digi_303.slcio",
    "muonGun_pT_2p0_2p1_digi_304.slcio",
    "muonGun_pT_2p0_2p1_digi_305.slcio",
    "muonGun_pT_2p0_2p1_digi_306.slcio",
    "muonGun_pT_2p0_2p1_digi_307.slcio",
    "muonGun_pT_2p0_2p1_digi_308.slcio",
    "muonGun_pT_2p0_2p1_digi_309.slcio",    
]
COLS = [
    "IBTrackerHits",
    "OBTrackerHits",
]
RELS = [
    "IBTrackerHitsRelations",
    "OBTrackerHitsRelations",
]
SPEED_OF_LIGHT = 299.792458  # mm/ns
MM_TO_UM = 1000.0


def main():
    df = get_df(DIGI_NAMES)
    print(df)
    with PdfPages("check.pdf") as pdf:
        plot(df, pdf)


def get_df(fnames):
    hits = []
    for fname in fnames:
        print(f"Processing file {fname} ...")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(fname)
        for i_event, event in enumerate(reader):
            for i_rel, relname in enumerate(RELS):
                rels = event.getCollection(relname)
                for rel in rels:
                    simhit, hit = rel.getTo(), rel.getFrom()
                    hits.append({
                        "i_rel": i_rel,
                        "sim_x": simhit.getPosition()[0],
                        "sim_y": simhit.getPosition()[1],
                        "sim_z": simhit.getPosition()[2],
                        "sim_t": simhit.getTime(),
                        "sim_cellid": simhit.getCellID0(),
                        "hit_x": hit.getPosition()[0],
                        "hit_y": hit.getPosition()[1],
                        "hit_z": hit.getPosition()[2],
                        "hit_t": hit.getTime()
                    })

    # merge
    df = pd.DataFrame(hits)

    # post-process
    df["hit_R"] = (df["hit_x"]**2 + df["hit_y"]**2 + df["hit_z"]**2)**0.5
    df["sim_R"] = (df["sim_x"]**2 + df["sim_y"]**2 + df["sim_z"]**2)**0.5
    df["sim_t_RC"] = df["sim_t"] - df["sim_R"] / SPEED_OF_LIGHT
    df["sim_system"] = np.right_shift(df["sim_cellid"], 0) & 0b1_1111
    df["sim_side"] = np.right_shift(df["sim_cellid"], 5) & 0b11
    df["sim_layer"] = np.right_shift(df["sim_cellid"], 7) & 0b11_1111
    df["sim_module"] = np.right_shift(df["sim_cellid"], 13) & 0b111_1111_1111
    df["sim_sensor"] = np.right_shift(df["sim_cellid"], 24) & 0b1111_1111

    return df


def plot(df, pdf):

    systems = df["i_rel"].unique()
    bins = np.linspace(-15, 15, 100)

    for system in systems:

        # diff in R
        _df = df[df["i_rel"] == system]
        fig, ax = plt.subplots()
        diff = _df["sim_R"] - _df["hit_R"]
        one_sigma_quantile = np.percentile(np.abs(diff), 68.27)
        one_sigma_quantile *= MM_TO_UM
        ax.hist(diff * MM_TO_UM, bins=bins)
        ax.text(0.95, 0.95, f"1sigma = {one_sigma_quantile:.1f} um", transform=ax.transAxes, ha="right", va="top")
        ax.set_xlabel("sim_R - hit_R (um)")
        ax.set_title(f"System {system}")
        pdf.savefig()
        plt.close()

        # diff in y when module=0
        _df = df[(df["i_rel"] == system) & (df["sim_module"] == 0)]
        fig, ax = plt.subplots()
        diff = _df["sim_y"] - _df["hit_y"]
        one_sigma_quantile = np.percentile(np.abs(diff), 68.27)
        one_sigma_quantile *= MM_TO_UM
        ax.hist(diff * MM_TO_UM, bins=bins)
        ax.text(0.95, 0.95, f"1sigma = {one_sigma_quantile:.1f} um", transform=ax.transAxes, ha="right", va="top")
        ax.set_xlabel("sim_y - hit_y (um)")
        ax.set_title(f"System {system}, module=0")
        pdf.savefig()
        plt.close()


if __name__ == "__main__":
    main()

