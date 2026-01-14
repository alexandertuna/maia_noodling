import inspect
import textwrap
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
from constants import ONE_POINT_FIVE_GEV, ONE_MM


class Plotter:

    def __init__(
        self,
        signal: bool,
        mcps: pd.DataFrame,
        doublets: pd.DataFrame,
        pdf: str,
    ):
        self.signal = signal
        self.mcps = mcps
        self.doublets = doublets
        self.pdf = pdf


    def plot(self):
        print(f"Writing plots to {self.pdf} ...")
        with PdfPages(self.pdf) as pdf:
            if self.signal:
                self.write_denominator_info(pdf)
                self.plot_efficiency_vs_kinematics(pdf)


    def write_denominator_info(self, pdf: PdfPages):
        text = f"Efficiency denominator:"
        function = inspect.getsource(self.get_denominator_mask)
        function = textwrap.dedent(function)
        fig, ax = plt.subplots(figsize=(8, 8))
        args = {"ha":"left", "va":"top", "fontfamily":"monospace"}
        ax.text(0.0, 0.9, text, **args, fontsize=16)
        ax.text(0.0, 0.8, function, **args, fontsize=10)
        ax.axis("off")
        pdf.savefig()
        plt.close()


    def plot_efficiency_vs_kinematics(self, pdf: PdfPages):

        bins = {
            "mcp_pt": np.linspace(0.0, 10.0, 201),
            "mcp_eta": np.linspace(-0.7, 0.7, 281),
            "mcp_phi": np.linspace(-3.2, 3.2, 321),
        }
        xlabel = {
            "mcp_pt": r"Muon $p_T$ [GeV]",
            "mcp_eta": r"Muon $\eta$",
            "mcp_phi": r"Muon $\phi$ [rad]",
        }

        # denominator
        dmask = self.get_denominator_mask()
        denom = self.mcps[dmask][["file", "i_event", "i_mcp", "mcp_pt", "mcp_eta", "mcp_phi"]]
        if denom.duplicated().any():
            raise ValueError("Denominator has duplicated rows!")

        # numerator
        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_module", # the phi-module
            "simhit_sensor", # the z-sensor
        ]

        # filter doublets to only those with same parent mcp
        self.doublets["i_mcp"] = self.doublets["i_mcp_lower"]
        same_parent = self.doublets["i_mcp_lower"] == self.doublets["i_mcp_upper"]
        doublets = self.doublets[same_parent][ doublet_cols + ["i_mcp"] ].drop_duplicates()

        # check if doublets's [file, i_event, i_mcp] is in denominator
        for kin in ["mcp_pt", "mcp_eta", "mcp_phi"]:
            for system in [5]:
                for doublelayer in [0]:
                    mask = (
                        (doublets["simhit_system"] == system) &
                        (doublets["simhit_layer_div_2"] == doublelayer)
                    )
                    doublet_keys = doublets[mask][["file", "i_event", "i_mcp"]].drop_duplicates()
                    merged = denom.merge(doublet_keys, on=["file", "i_event", "i_mcp"], how="inner")

                    n_denom, edges = np.histogram(denom[kin], bins=bins[kin])
                    n_num, edges = np.histogram(merged[kin], bins=bins[kin])
                    efficiency = np.divide(n_num, n_denom, out=np.zeros_like(n_num, dtype=float), where=n_denom!=0)
                    centers = 0.5 * (edges[1:] + edges[:-1])
                    fig, ax = plt.subplots()
                    ax.plot(
                        centers,
                        efficiency,
                        marker="o",
                        markersize=1,
                        linestyle="-",
                        color="dodgerblue",
                    )
                    ax.set_xlabel(xlabel[kin])
                    ax.set_ylabel("Doublet finding efficiency")
                    ax.set_title(f"System {system} Double Layer {doublelayer}")
                    ax.set_ylim(0.7, 1.03)
                    pdf.savefig()
                    plt.close()


    def get_denominator_mask(self):
        mask = (
            (self.mcps["mcp_pdg"].isin([MUON, ANTIMUON])) &
            (self.mcps["mcp_q"] != 0) &
            (self.mcps["mcp_pt"] > ONE_POINT_FIVE_GEV) &
            (self.mcps["mcp_vertex_r"] < ONE_MM) &
            (np.abs(self.mcps["mcp_vertex_z"]) < ONE_MM) &
            (self.mcps["mcp_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
            (np.abs(self.mcps["mcp_eta"]) < BARREL_TRACKER_MAX_ETA)
        )
        return mask
