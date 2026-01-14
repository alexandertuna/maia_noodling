import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import FancyArrowPatch
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
    "axes.axisbelow": True,
    "grid.linewidth": 0.5,
    "grid.alpha": 0.1,
    "grid.color": "gray",
    "figure.subplot.left": 0.14,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

from constants import MUON, ANTIMUON
from constants import BARREL_TRACKER_MAX_ETA
from constants import BARREL_TRACKER_MAX_RADIUS
from constants import ONE_GEV, ONE_MM


class Plotter:

    def __init__(
        self,
        mcps: pd.DataFrame,
        doublets: pd.DataFrame,
        pdf: str,
    ):
        self.mcps = mcps
        self.doublets = doublets
        self.pdf = pdf


    def plot(self):
        print(f"Writing plots to {self.pdf} ...")
        with PdfPages(self.pdf) as pdf:
            self.plot_efficiency_vs_eta(pdf)


    def plot_efficiency_vs_eta(self, pdf: PdfPages):

        # denominator
        dmask = (
            (self.mcps["mcp_pdg"].isin([MUON, ANTIMUON])) &
            (self.mcps["mcp_q"] != 0) &
            (self.mcps["mcp_pt"] > 2 * ONE_GEV) &
            (self.mcps["mcp_vertex_r"] < ONE_MM) &
            (np.abs(self.mcps["mcp_vertex_z"]) < ONE_MM) &
            (self.mcps["mcp_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
            (np.abs(self.mcps["mcp_eta"]) < BARREL_TRACKER_MAX_ETA)
        )
        denom = self.mcps[dmask][["file", "i_event", "i_mcp", "mcp_eta"]]
        if denom.duplicated().any():
            raise ValueError("Denominator has duplicated rows!")
        print(f"Denominator size: {len(denom)} / {len(self.mcps)} total mcps")
        print(self.mcps[dmask])

        # numerator
        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_module", # the phi-module
            "simhit_sensor", # the z-sensor
        ]
        print("*"*50)
        print(f"self.doublets: {len(self.doublets)} rows ->")
        print(self.doublets)

        self.doublets["i_mcp"] = self.doublets["i_mcp_lower"]
        same_parent = self.doublets["i_mcp_lower"] == self.doublets["i_mcp_upper"]
        doublets = self.doublets[same_parent][ doublet_cols + ["i_mcp"] ].drop_duplicates()

        bins = np.linspace(-0.7, 0.7, 281)

        # check if doublets's [file, i_event, i_mcp] is in denominator
        for system in [5]:
            for doublelayer in [0]:
                mask = (
                    (doublets["simhit_system"] == system) &
                    (doublets["simhit_layer_div_2"] == doublelayer)
                )
                print("="*50)
                print(f"doublets[mask]: {len(doublets[mask])} rows for system {system} doublelayer {doublelayer} ->")
                print(doublets[mask])
                doublet_keys = doublets[mask][["file", "i_event", "i_mcp"]].drop_duplicates()
                merged = denom.merge(doublet_keys, on=["file", "i_event", "i_mcp"], how="inner")
                print(f"Numerator size: {len(merged)} / {len(denom)} denominator mcps for system {system} doublelayer {doublelayer}")
                print("="*50)
                print("merged:")
                print(merged)

                n_denom, edges = np.histogram(denom["mcp_eta"], bins=bins)
                n_num, edges = np.histogram(merged["mcp_eta"], bins=bins)
                efficiency = np.divide(n_num, n_denom, out=np.zeros_like(n_num, dtype=float), where=n_denom!=0)
                centers = 0.5 * (edges[1:] + edges[:-1])
                fig, ax = plt.subplots()
                ax.plot(centers, efficiency, marker="o", markersize=1, linestyle="-")
                ax.set_xlabel("Muon eta")
                ax.set_ylabel("Doublet finding efficiency")
                ax.set_title(f"System {system} Double Layer {doublelayer}")
                ax.set_ylim(0, 1.1)
                pdf.savefig()
                plt.close()


                # fig, ax = plt.subplots()
                # ax.plot


                # simhit_layer_div_2
        # doublet_mcp_indices = pd.DataFrame({
        #     "file": self.doublets["file"],
        #     "i_event": self.doublets["i_event"],
        #     "i_mcp": self.doublets["i_mcp_lower" if same_parent.all() else "i_mcp_upper"],
        # }).drop_duplicates()
        # doublet_keys = self.doublets[["file", "i_event", "i_mcp_lower"]].drop_duplicates()
        # doublet_keys.rename(columns={"i_mcp_lower":"i_mcp"}, inplace=True)
        # merged = denom.merge(doublet_keys, on=["file", "i_event", "i_mcp"], how="inner")
        # print(f"Numerator size: {len(merged)} / {len(denom)} denominator mcps")
