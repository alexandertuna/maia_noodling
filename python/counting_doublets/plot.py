import inspect
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors
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
    "figure.subplot.left": 0.14,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

from constants import MUON, ANTIMUON
from constants import BARREL_TRACKER_MAX_ETA
from constants import BARREL_TRACKER_MAX_RADIUS
from constants import ONE_POINT_FIVE_GEV, ONE_MM
from constants import SYSTEMS, DOUBLELAYERS, LAYERS, NICKNAMES
from constants import REQ_PASSTHROUGH, REQ_RZ, REQ_XY, REQ_RZ_XY
from constants import DOUBLET_REQS
from constants import MIN_COSTHETA, MIN_SIMHIT_PT_FRACTION, MAX_TIME


class Plotter:

    def __init__(
        self,
        signal: bool,
        mcps: pd.DataFrame,
        simhits: pd.DataFrame,
        doublets: pd.DataFrame,
        pdf: str,
    ):
        self.signal = signal
        self.mcps = mcps
        self.simhits = simhits
        self.doublets = doublets
        self.pdf = pdf
        self.add_doublet_mcp_features()


    def plot(self):
        print(f"Writing plots to {self.pdf} ...")
        with PdfPages(self.pdf) as pdf:
            self.plot_layer_occupancy(pdf)
            self.plot_doublet_occupancy(pdf)
            if self.signal:
                self.write_denominator_info(pdf)
                self.plot_efficiency_vs_kinematics(pdf)
                self.plot_doublet_quality_efficiency(pdf)


    def plot_layer_occupancy(self, pdf: PdfPages):
        for system in SYSTEMS:
            for layer in LAYERS:
                mask = (
                    (self.simhits["simhit_system"] == system) &
                    (self.simhits["simhit_layer"] == layer)
                )
                print(f"Occupancy of {NICKNAMES[system]} layer {layer}: {mask.sum()} sim hits")
                simhits = self.simhits[mask]
                bins = [
                    np.arange(-0.5, simhits["simhit_module"].max()+1.5, 1),
                    np.arange(-0.5, simhits["simhit_sensor"].max()+1.5, 1),
                ]
                fig, ax = plt.subplots()
                _, _, _, im = ax.hist2d(
                    simhits["simhit_module"],
                    simhits["simhit_sensor"],
                    bins=bins,
                    cmap="gist_rainbow",
                    norm=colors.LogNorm(vmin=0.9),
                )

                # Major ticks (decades)
                # Minor ticks (2–9 per decade)

                ax.set_xlabel("Phi module")
                ax.set_ylabel("Z sensor")
                ax.set_title(f"{NICKNAMES[system]}, layer {layer}")
                cbar = fig.colorbar(im, ax=ax, pad=0.01, label="Number of sim. hits")
                # cbar.ax.minorticks_on()
                # cbar.ax.tick_params(which='minor', length=4, color='black')
                # cbar.ax.yaxis.set_major_locator(LogLocator(base=10))
                # cbar.ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1))
                # cbar.ax.yaxis.set_minor_formatter(NullFormatter())
                # cbar.ax.tick_params(which="minor", color="black")
                # print(cbar.ax.yaxis.get_scale())
                pdf.savefig()
                plt.close()


    def requirements(self, req: str) -> tuple[str, pd.DataFrame]:
        # return description and mask
        if req == REQ_PASSTHROUGH:
            text = "No requirement"
            mask = np.ones(len(self.doublets), dtype=bool)
        elif req == REQ_XY:
            text = "|dphi| < 0.55rad"
            mask = np.abs(self.doublets["dphi"]) < 0.55
        elif req == REQ_RZ:
            text = "|dz| < 60mm"
            mask = np.abs(self.doublets["intercept_rz"]) < 60
        elif req == REQ_RZ_XY:
            text = "|dphi| < 0.55rad, |dz| < 60mm"
            mask = (
                (np.abs(self.doublets["intercept_rz"]) < 60) &
                (np.abs(self.doublets["dphi"]) < 0.55)
            )
        else:
            raise ValueError(f"Unknown requirement: {req}")
        return text, mask


    def plot_doublet_occupancy(self, pdf: PdfPages):
        for system in SYSTEMS:
            for doublelayer in DOUBLELAYERS:
                zmax = None
                for req in DOUBLET_REQS:
                    req_text, req_mask = self.requirements(req)
                    print(f"Occupancy of {NICKNAMES[system]} doublelayer {doublelayer}, {req}: {req_mask.sum()} doublets")
                    layers = [doublelayer * 2, doublelayer * 2 + 1]
                    mask = (
                        (self.doublets["simhit_system"] == system) &
                        (self.doublets["simhit_layer_div_2"] == doublelayer) &
                        req_mask
                    )
                    doublets = self.doublets[mask]
                    bins = [
                        np.arange(-0.5, doublets["simhit_module"].max()+1.5, 1),
                        np.arange(-0.5, doublets["simhit_sensor"].max()+1.5, 1),
                    ]
                    fig, ax = plt.subplots()
                    h2d, _, _, im = ax.hist2d(
                        doublets["simhit_module"],
                        doublets["simhit_sensor"],
                        bins=bins,
                        cmap="gist_rainbow",
                        norm=colors.LogNorm(vmin=0.9),
                    )
                    if zmax is None:
                        zmax = h2d.max()
                    im.set_clim(0.9, zmax)
                    ax.set_xlabel("Phi module")
                    ax.set_ylabel("Z sensor")
                    ax.set_title(f"{NICKNAMES[system]}, layers {layers}, {req_text}")
                    fig.colorbar(im, ax=ax, label="Number of doublets", pad=0.01)
                    pdf.savefig()
                    plt.close()


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
                    n_numer, edges = np.histogram(merged[kin], bins=bins[kin])
                    efficiency = np.divide(n_numer, n_denom, out=np.zeros_like(n_numer, dtype=float), where=n_denom!=0)
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


    def add_doublet_mcp_features(self):
        # add mcp features when the doublet i_mcp_lower and i_mcp_upper match
        # otherwise, assign 0
        mcp_cols = [
            "mcp_p",
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
            "mcp_pdg",
            "mcp_q",
            "mcp_vertex_r",
            "mcp_vertex_z",
            "mcp_endpoint_r",
        ]
        if not self.signal:
            self.doublets[mcp_cols] = 0
            return
        merged = self.doublets.merge(
            self.mcps[["file", "i_event", "i_mcp", *mcp_cols]],
            left_on=["file", "i_event", "i_mcp_lower"],
            right_on=["file", "i_event", "i_mcp"],
            how="left",
            validate="many_to_one",
        ).drop(columns=["i_mcp"])
        mask = merged["i_mcp_lower"].eq(merged["i_mcp_upper"])
        self.doublets[mcp_cols] = merged[mcp_cols].where(mask, 0).fillna(0)


    def plot_doublet_quality_efficiency(self, pdf: PdfPages):

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

        # only consider truth-match doublets
        baseline = (
            first_exit_mask(self.doublets) &
            (self.doublets["i_mcp_lower"] == self.doublets["i_mcp_upper"]) &
            (self.doublets["mcp_pdg"].isin([MUON, ANTIMUON])) &
            (self.doublets["mcp_q"] != 0) &
            (self.doublets["mcp_pt"] > ONE_POINT_FIVE_GEV) &
            (np.abs(self.doublets["mcp_eta"]) < BARREL_TRACKER_MAX_ETA) &
            (self.doublets["mcp_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
            (self.doublets["mcp_vertex_r"] < ONE_MM) &
            (np.abs(self.doublets["mcp_vertex_z"]) < ONE_MM)
        )

        # todo: add comment
        for kin in ["mcp_pt", "mcp_eta", "mcp_phi"]:

            for system in SYSTEMS:

                for doublelayer in DOUBLELAYERS:

                    print(f"Plotting doublet quality efficiency vs {kin}, system {system}, doublelayer {doublelayer} ...")

                    geo_mask = (
                        (self.doublets["simhit_system"] == system) &
                        (self.doublets["simhit_layer_div_2"] == doublelayer)
                    )

                    for req in DOUBLET_REQS:
                        req_text, req_mask = self.requirements(req)
                        denom = self.doublets[baseline & geo_mask]
                        numer = self.doublets[baseline & geo_mask & req_mask]

                        n_denom, edges = np.histogram(denom[kin], bins=bins[kin])
                        n_numer, edges = np.histogram(numer[kin], bins=bins[kin])
                        efficiency = np.divide(n_numer, n_denom, out=np.zeros_like(n_numer, dtype=float), where=n_denom!=0)
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
                        ax.set_title(f"System {system} Double Layer {doublelayer}: {req_text}")
                        ax.set_ylim(0.98, 1.001)
                        pdf.savefig()
                        plt.close()



def first_exit_mask(doublets: pd.DataFrame) -> pd.Series:
    return (
        (doublets["simhit_costheta_lower"] > MIN_COSTHETA) &
        (doublets["simhit_costheta_upper"] > MIN_COSTHETA) &
        (doublets["simhit_t_corrected_lower"] < MAX_TIME) &
        (doublets["simhit_t_corrected_upper"] < MAX_TIME) &
        (doublets["simhit_p_lower"] / doublets["mcp_p"] > MIN_SIMHIT_PT_FRACTION) &
        (doublets["simhit_p_upper"] / doublets["mcp_p"] > MIN_SIMHIT_PT_FRACTION)
    )

