import inspect
import textwrap
import warnings
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

from constants import BARREL_TRACKER_MAX_ETA
from constants import BARREL_TRACKER_MAX_RADIUS
from constants import ONE_GEV, ONE_MM
from constants import INSIDE_BOUNDS, UNDEFINED_BOUNDS, POSSIBLE_BOUNDS
from constants import MIN_SIMHIT_PT_FRACTION, MAX_TIME, MIN_COSTHETA
from slcio_to_hits import filter_dataframe

INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5
SYSTEMS = [
    INNER_TRACKER_BARREL,
    OUTER_TRACKER_BARREL,
]
LAYERS = range(8)
RADIUS = {
    INNER_TRACKER_BARREL: [127, 127+2, 167, 167+2, 510, 510+2, 550, 550+2],
    OUTER_TRACKER_BARREL: [819, 819+2, 899, 899+2, 1366, 1366+2, 1446, 1446+2],
}
N_SENSORS = {
    INNER_TRACKER_BARREL: [32, 32, 32, 32, 46, 46, 46, 46],
    OUTER_TRACKER_BARREL: [42, 42, 42, 42, 42, 42, 42, 42],
}
SENSOR_SIZE = {
    INNER_TRACKER_BARREL: 30.0,
    OUTER_TRACKER_BARREL: 60.0,
}
N_MODULES = {
    INNER_TRACKER_BARREL: [15*2, 15*2, 20*2, 20*2, 58*2, 58*2, 62*2, 62*2],
    OUTER_TRACKER_BARREL: [48*2, 48*2, 52*2, 52*2, 80*2, 80*2, 84*2, 84*2],
}
SYSTEM_ABBREV = {
    INNER_TRACKER_BARREL: "ITB",
    OUTER_TRACKER_BARREL: "OTB",
}


class Plotter:


    def __init__(self, df: pd.DataFrame, pdf: str):
        self.df = df
        self.pdf = pdf
        self.n_phi_for_modulo = 4
        self.post_process()


    def post_process(self):

        # phi_mod for plotting wrapped-around phi modules
        for system in SYSTEMS:
            for layer in LAYERS:
                abbrev = SYSTEM_ABBREV[system]
                n_modules = N_MODULES[system][layer]
                period = (2 * np.pi) / (n_modules / self.n_phi_for_modulo)
                self.df[f"mcp_phi_mod_{abbrev}_{layer}"] = (self.df["mcp_phi"] + 2 * np.pi) % period

        # phi_mod for plotting wrapped-around phi modules
        lookup = (
            pd.DataFrame(
                [(sys, layer, N_MODULES[sys][layer])
                for sys in N_MODULES
                for layer in range(len(N_MODULES[sys]))],
                columns=["simhit_system", "simhit_layer", "n_modules"],
            )
        )
        relevant_cols = ["simhit_system", "simhit_layer"]
        n_modules = (
            self.df[relevant_cols]
            .merge(lookup, on=relevant_cols, how="left")["n_modules"]
        )
        period = (2 * np.pi) / (n_modules / self.n_phi_for_modulo)
        self.df[f"simhit_phi_mod"] = (self.df["simhit_phi"] + 2*np.pi) % period


    def plot(self):
        with PdfPages(self.pdf) as pdf:
            self.data_format(pdf)
            self.efficiency_denominator(pdf)
            self.efficiency_numerator(pdf)
            self.plot_mcp_pt(pdf)
            self.plot_mcp_eta(pdf)
            self.plot_mcp_phi(pdf)
            # self.plot_simhit_time(pdf)
            # self.plot_simhit_time_corrected(pdf)
            # # self.plot_simhit_distance(pdf)
            # self.plot_simhit_xy(pdf)
            # self.plot_simhit_rz(pdf)
            # self.plot_simhit_p(pdf)
            # self.plot_simhit_pt(pdf)
            # self.plot_simhit_costheta(pdf)
            # self.plot_simhit_costheta_vs_time(pdf)
            # self.plot_simhit_p_vs_time(pdf)
            # self.plot_simhit_p_vs_costheta(pdf)
            self.plot_layer_efficiency_vs_sim(pdf)
            # self.plot_weird_radius_hits(pdf)
            self.plot_doublet_efficiency_vs_sim(pdf)
            self.plot_r_phi_mod(pdf)


    def data_format(self, pdf: PdfPages):
        text = "Data format: Pandas DataFrame"
        columns = [
            "file",
            "i_event",
            "i_mcp",
            "simhit",
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
            "mcp_pdg",
            "simhit_system",
            "simhit_layer",
            "simhit_module",
        ]
        dstr = self.df.to_string(
            columns=columns,
            max_rows=50,
        )
        cols = "All columns: " + ", ".join([str(col) for col in self.df.columns.tolist()])
        cols = textwrap.fill(cols, width=150)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(-0.12, 0.95, text, ha="left")
        ax.text(-0.12, 0.90, dstr, ha="left", va="top", fontfamily="monospace", fontsize=6)
        ax.text(-0.12, 0.05, cols, ha="left", va="top", fontfamily="monospace", fontsize=6)
        ax.axis("off")
        pdf.savefig()
        plt.close()


    def efficiency_denominator(self, pdf: PdfPages):
        text = "Efficiency denominator"
        code = inspect.getsource(filter_dataframe)
        code = textwrap.dedent(code)
        texts = [
            f" * Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$",
            f" * non-zero charge",
            f" * $p_T$ > {ONE_GEV} GeV",
            f" * Vertex r < {ONE_MM} mm",
            f" * abs(Vertex z) < {ONE_MM} mm",
            f" * Endpoint r > {BARREL_TRACKER_MAX_RADIUS} mm",
            f" * abs($\\eta$) < {BARREL_TRACKER_MAX_ETA}",
        ]
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.0, 0.8, text, ha="left")
        ax.text(0.0, 0.7, code, ha="left", va="top", fontfamily="monospace", fontsize=10)
        ax.axis("off")
        pdf.savefig()
        plt.close()


    def efficiency_numerator(self, pdf: PdfPages):
        text = f"Efficiency numerator:"
        numer = inspect.getsource(numerator_mask)
        numer = textwrap.dedent(numer)
        first = inspect.getsource(first_exit_mask)
        first = textwrap.dedent(first)
        fig, ax = plt.subplots(figsize=(8, 8))
        args = {"ha":"left", "va":"top", "fontfamily":"monospace", "fontsize":10}
        ax.text(0.0, 0.9, text, **args)
        ax.text(0.0, 0.8, numer, **args)
        ax.text(0.0, 0.4, first, **args)
        ax.text(0.0, 0.20, f"MIN_COSTHETA={MIN_COSTHETA}", **args)
        ax.text(0.0, 0.15, f"MIN_SIMHIT_PT_FRACTION={MIN_SIMHIT_PT_FRACTION}", **args)
        ax.text(0.0, 0.10, f"MAX_TIME={MAX_TIME}", **args)
        ax.axis("off")
        pdf.savefig()
        plt.close()


    def plot_weird_radius_hits(self, pdf: PdfPages):
        for (r_lo, r_hi) in [
            (140.0, 160.0),
            (330.0, 350.0),
            (520.0, 540.0),
        ]:
            mask = (
                self.df["simhit"].astype(bool) &
                (self.df["simhit_r"] > r_lo) &
                (self.df["simhit_r"] < r_hi)
            )
            feats = [
                "simhit_r",
                "simhit_pathlength",
            ]
            xlabel = {
                "simhit_r": "Sim. hit radius [mm]",
                "simhit_pathlength": "Sim. hit pathlength [mm]",
            }
            bins = {
                "simhit_r": np.linspace(r_lo, r_hi, 201),
                "simhit_pathlength": np.linspace(0, 0.4, 201),
            }
            fig, axs = plt.subplots(figsize=(16, 8), ncols=2)
            for ax, feat in zip(axs, feats):
                ax.hist(self.df[mask][feat],
                        bins=bins[feat],
                        histtype="stepfilled",
                        color="dodgerblue",
                        alpha=0.9,
                        )
                ax.set_xlabel(xlabel[feat])
                ax.set_ylabel("Counts")
                ax.set_title(f"Sim. hits with radius {r_lo}-{r_hi} mm")

            fig.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.09, wspace=0.15)
            pdf.savefig()
            plt.close()


    def plot_mcp_pt(self, pdf: PdfPages):
        mask = ~(self.df["simhit"].astype(bool))
        bins = np.linspace(0, 10, 101)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["mcp_pt"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.set_xlabel("Simulated $p_T$ [GeV]")
        ax.set_ylabel("Counts")
        ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_mcp_eta(self, pdf: PdfPages):
        mask = ~(self.df["simhit"].astype(bool))
        bins = np.linspace(-0.9, 0.9, 181)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["mcp_eta"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.set_xlabel("Simulated eta")
        ax.set_ylabel("Counts")
        ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_mcp_phi(self, pdf: PdfPages):
        mask = ~(self.df["simhit"].astype(bool))
        bins = np.linspace(-3.2, 3.2, 161)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["mcp_phi"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.set_xlabel("Simulated phi")
        ax.set_ylabel("Counts")
        ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_simhit_time(self, pdf: PdfPages):
        mask = self.df["simhit"].astype(bool)
        bins = np.linspace(0, 40, 201)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["simhit_t"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                label="All hits",
                )
        ax.set_xlabel("Sim. hit time [ns]")
        ax.set_ylabel("Counts")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_simhit_time_corrected(self, pdf: PdfPages):
        mask = self.df["simhit"].astype(bool)
        bins = np.linspace(0, 40, 201)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["simhit_t_corrected"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                label="All hits",
                )
        # add vertical line at MAX_TIME
        ax.axvline(MAX_TIME, color="red", linestyle="--")
        ax.set_xlabel(r"Sim. hit time minus $R/c$ [ns]")
        ax.set_ylabel("Counts")
        ax.set_title(f"Require sim. hit time < {MAX_TIME}ns")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_simhit_distance(self, pdf: PdfPages):
        mask = self.df["simhit"].astype(bool)
        bins = np.linspace(-300, 300, 301)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["simhit_distance"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.set_xlabel("Sim. hit distance to surface [mm]")
        ax.set_ylabel("Counts")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_simhit_xy(self, pdf: PdfPages):
        mask = self.df["simhit"].astype(bool)
        bins = [
            np.linspace(-1500, 1500, 451),
            np.linspace(-1500, 1500, 451),
        ]
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df[mask]["simhit_r"] * np.cos(self.df[mask]["simhit_phi"]),
            self.df[mask]["simhit_r"] * np.sin(self.df[mask]["simhit_phi"]),
            bins=bins,
            cmap="gist_rainbow",
            cmin=0.5,
        )
        fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
        ax.set_xlabel("Sim. hit x [mm]")
        ax.set_ylabel("Sim. hit y [mm]")
        fig.subplots_adjust(left=0.15, right=0.93, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_simhit_rz(self, pdf: PdfPages):
        mask = self.df["simhit"].astype(bool)
        bins = [
            np.linspace(-2000, 2000, 401),
            np.linspace(0, 1500, 451),
        ]
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df[mask]["simhit_z"],
            self.df[mask]["simhit_r"],
            bins=bins,
            cmap="gist_rainbow",
            cmin=0.5,
        )
        fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
        ax.set_xlabel("Sim. hit z [mm]")
        ax.set_ylabel("Sim. hit r [mm]")
        fig.subplots_adjust(left=0.15, right=0.93, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_simhit_p(self, pdf: PdfPages):
        print("Plotting sim hit p / mcp p...")
        mask = self.df["simhit"].astype(bool)
        bins = np.linspace(-0.05, 1.05, 111)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["simhit_p"] / self.df[mask]["mcp_p"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.set_xlabel("Sim. hit $p$ / Sim. $p$")
        ax.set_ylabel("Counts")
        ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_simhit_pt(self, pdf: PdfPages):
        print("Plotting sim hit pt / mcp pt...")
        mask = self.df["simhit"].astype(bool)
        bins = np.linspace(-0.05, 1.05, 111)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["simhit_pt"] / self.df[mask]["mcp_pt"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.set_xlabel("Sim. hit $p_T$ / Sim. $p_T$")
        ax.set_ylabel("Counts")
        ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_simhit_costheta(self, pdf: PdfPages):
        print("Plotting sim hit costheta ...")
        mask = self.df["simhit"].astype(bool)
        bins = np.linspace(-1, 1, 101)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["simhit_costheta"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.set_xlabel(r"Sim. hit cos($\theta$) between $r$ and $p$")
        ax.set_ylabel("Counts")
        ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_simhit_costheta_vs_time(self, pdf: PdfPages):
        print("Plotting sim hit costheta vs time ...")
        mask = self.df["simhit"].astype(bool)
        bins = [
            np.linspace(0, 40, 121),
            np.linspace(-1.05, 1.05, 111),
        ]
        for simhit_t in ["simhit_t", "simhit_t_corrected"]:
            fig, ax = plt.subplots(figsize=(8,8))
            _, _, _, im = ax.hist2d(
                self.df[mask][simhit_t],
                self.df[mask]["simhit_costheta"],
                bins=bins,
                cmap="gist_rainbow",
                cmin=0.5,
                norm=colors.LogNorm(vmin=1),
                )
            xlabel = "Sim. hit time [ns]" + (r" minus $R/c$" if "corrected" in simhit_t else "")
            fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
            ax.set_xlabel(xlabel)
            ax.set_ylabel(r"Sim. hit cos($\theta$) between $r$ and $p$")
            ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
            pdf.savefig()
            plt.close()


    def plot_simhit_p_vs_time(self, pdf: PdfPages):
        print("Plotting sim hit p vs time ...")
        mask = self.df["simhit"].astype(bool)
        bins = [
            np.linspace(0, 40, 121),
            np.linspace(-0.05, 1.05, 111),
        ]
        for simhit_t in ["simhit_t", "simhit_t_corrected"]:
            fig, ax = plt.subplots(figsize=(8,8))
            _, _, _, im = ax.hist2d(
                self.df[mask][simhit_t],
                self.df[mask]["simhit_p"] / self.df[mask]["mcp_p"],
                bins=bins,
                cmap="gist_rainbow",
                cmin=0.5,
                norm=colors.LogNorm(vmin=1),
                )
            xlabel = "Sim. hit time [ns]" + (r" minus $R/c$" if "corrected" in simhit_t else "")
            fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
            ax.set_xlabel(xlabel)
            ax.set_ylabel("Sim. hit $p$ / Sim. $p$")
            ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
            pdf.savefig()
            plt.close()


    def plot_simhit_p_vs_costheta(self, pdf: PdfPages):
        print("Plotting sim hit p vs costheta ...")
        mask = self.df["simhit"].astype(bool)
        bins = [
            np.linspace(-1.05, 1.05, 111),
            np.linspace(-0.05, 1.05, 111),
        ]
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df[mask]["simhit_costheta"],
            self.df[mask]["simhit_p"] / self.df[mask]["mcp_p"],
            bins=bins,
            cmap="gist_rainbow",
            cmin=0.5,
            norm=colors.LogNorm(vmin=1),
            )
        fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
        ax.set_xlabel(r"Sim. hit cos($\theta$) between $r$ and $p$")
        ax.set_ylabel("Sim. hit $p$ / Sim. $p$")
        ax.set_title(f"Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$")
        pdf.savefig()
        plt.close()


    def plot_layer_efficiency_vs_sim(self, pdf: PdfPages):
        bins = {
            "mcp_pt": np.linspace(0, 10, 101),
            "mcp_eta": np.linspace(-0.7, 0.7, 281),
            "mcp_phi": np.linspace(-3.2, 3.2, 161),
            ("mcp_pt", "mcp_phi"): [np.linspace(0, 10, 101),
                                    np.linspace(-3.2, 3.2, 161)],
            ("mcp_eta", "mcp_phi"): [np.linspace(-0.7, 0.7, 281),
                                     np.linspace(-3.2, 3.2, 161)],
        }
        system_name = {
            INNER_TRACKER_BARREL: "Inner Tracker Barrel",
            OUTER_TRACKER_BARREL: "Outer Tracker Barrel",
        }
        xlabel = {
            "mcp_pt": "Simulated $p_T$ [GeV]",
            "mcp_eta": "Simulated eta",
            "mcp_phi": "Simulated phi",
        }

        # mask for first exit / arc / path
        first_exit = first_exit_mask(self.df)

        # 1d plots showing cut values
        mask = numerator_mask(self.df, SYSTEMS, LAYERS) & first_exit
        fig, ax = plt.subplots(figsize=(8,8), ncols=2, nrows=2)
        ax[0, 0].hist(self.df[mask]["simhit_t_corrected"], bins=np.linspace(0, 10, 101))
        ax[0, 1].hist(self.df[mask]["simhit_costheta"], bins=np.linspace(-1, 1, 101))
        ax[1, 0].hist(self.df[mask]["simhit_p"] / self.df[mask]["mcp_p"], bins=np.linspace(0, 1, 101))
        ax[1, 1].hist(self.df[mask]["simhit_inside_bounds"], bins=np.linspace(min(POSSIBLE_BOUNDS) - 0.5,
                                                                              max(POSSIBLE_BOUNDS) + 0.5,
                                                                              len(POSSIBLE_BOUNDS) + 1))
        ax[0, 0].set_ylabel("Counts")
        ax[0, 1].set_ylabel("Counts")
        ax[1, 0].set_ylabel("Counts")
        ax[1, 1].set_ylabel("Counts")
        ax[0, 0].semilogy()
        ax[0, 1].semilogy()
        ax[1, 0].semilogy()
        ax[1, 1].semilogy()
        ax[0, 0].set_ylim([1, None])
        ax[0, 1].set_ylim([1, None])
        ax[1, 0].set_ylim([1, None])
        ax[1, 1].set_ylim([1, None])
        ax[0, 0].set_xlabel("Sim. hit time minus $R/c$ [ns]")
        ax[0, 1].set_xlabel(r"Sim. hit cos$\theta$ between $r$ and $p$")
        ax[1, 0].set_xlabel(r"Sim. hit $p$ / Sim. $p$")
        ax[1, 1].set_xticks(POSSIBLE_BOUNDS)
        ax[1, 1].set_xticklabels(["Outside bounds", "Inside bounds", "Undefined"], rotation=10, fontsize=10)
        fig.suptitle("Distributions after all cuts")
        fig.subplots_adjust(left=0.1, wspace=0.3)
        pdf.savefig()
        plt.close()

        # denominator of efficiency
        mask_denom = ~(self.df["simhit"].astype(bool))
        df_denom = self.df[mask_denom]
        if df_denom.duplicated().any():
            warnings.warn("Warning: duplicates found in denominator dataframe!")

        for kinematic in [
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
            ("mcp_pt", "mcp_phi"),
            ("mcp_eta", "mcp_phi"),
        ]:

            print(f"Plotting sim hit efficiency vs {kinematic}...")
            for system in SYSTEMS:

                for layer in LAYERS:

                    # nb: dont double-count if >1 hits on a layer
                    mask_numer = numerator_mask(self.df, [system], [layer]) & first_exit
                    subset = ["file", "i_event", "i_mcp", "simhit_system", "simhit_layer"]
                    df_numer = self.df[mask_numer].drop_duplicates(subset=subset)

                    is2d = isinstance(kinematic, tuple) and len(kinematic) == 2

                    # calculate efficiency
                    if is2d:
                        counts_denom, _, _ = np.histogram2d(
                            df_denom[kinematic[0]],
                            df_denom[kinematic[1]],
                            bins=bins[kinematic],
                        )
                        counts_numer, _, _ = np.histogram2d(
                            df_numer[kinematic[0]],
                            df_numer[kinematic[1]],
                            bins=bins[kinematic],
                        )
                        efficiency = np.divide(
                            counts_numer,
                            counts_denom,
                            out=np.full_like(counts_denom, 0.0, dtype=float),
                            where=(counts_denom > 0.0),
                        )
                        xedges, yedges = bins[kinematic]
                        fig, ax = plt.subplots(figsize=(8, 8))
                        mesh = ax.pcolormesh(
                            xedges,
                            yedges,
                            efficiency.T,
                            cmap="afmhot",
                            vmin=0.945,
                            vmax=1.005,
                        )
                        fig.colorbar(mesh, ax=ax, pad=0.01, label="Sim. hit double-layer efficiency")
                        ax.set_xlabel(xlabel[kinematic[0]])
                        ax.set_ylabel(xlabel[kinematic[1]])
                        ax.set_title(f"{system_name[system]}, layer {layer}")
                        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                        pdf.savefig()
                        plt.close()

                    else:
                        counts_denom, _ = np.histogram(df_denom[kinematic], bins=bins[kinematic])
                        counts_numer, _ = np.histogram(df_numer[kinematic], bins=bins[kinematic])
                        efficiency = np.divide(
                            counts_numer,
                            counts_denom,
                            out=np.full_like(counts_denom, 0.0, dtype=float),
                            where=(counts_numer > 0.0),
                        )
                        bin_centers = (bins[kinematic][1:] + bins[kinematic][:-1]) / 2.0

                        fig, ax = plt.subplots(figsize=(8, 8))
                        ax.plot(
                            bin_centers,
                            efficiency,
                            marker="o",
                            markersize=2,
                            linestyle="-",
                            linewidth=1,
                            color="dodgerblue",
                        )
                        ax.set_ylim(0.95, 1.005)
                        ax.set_xlabel(xlabel[kinematic])
                        ax.set_ylabel(f"Sim. hit efficiency with $t_{{corrected}}$ < {MAX_TIME} ns")
                        ax.set_title(f"{system_name[system]}, layer {layer}")
                        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                        pdf.savefig()
                        plt.close()


    def plot_r_phi_mod(self, pdf: PdfPages):

        first_exit = first_exit_mask(self.df)

        for system in SYSTEMS:

            for double_layers in [
                [0, 1],
                [2, 3],
                [4, 5],
                [6, 7],
            ]:
                # compute period for phi mod
                n_modules = N_MODULES[system][double_layers[0]]
                period = (2 * np.pi) / (n_modules / self.n_phi_for_modulo)

                print("Plotting sim hit rphi when modding ...")
                layer_mask = (
                    (self.df["simhit"].astype(bool)) &
                    (self.df["simhit_inside_bounds"].isin([INSIDE_BOUNDS, UNDEFINED_BOUNDS])) &
                    (self.df["simhit_system"] == system) &
                    (self.df["simhit_layer_div_2"].isin([dl // 2 for dl in double_layers]))
                )
                mask = layer_mask & first_exit
                fig, ax = plt.subplots(figsize=(8, 8))
                _, _, _, im = ax.hist2d(
                    self.df[mask][f"simhit_phi_mod"],
                    self.df[mask][f"simhit_r"],
                    bins=[200, 200],
                    cmap="gist_rainbow",
                    cmin=0.5,
                )
                fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
                ax.set_xlabel(f"Sim. hit phi mod {period:.4f} [rad]")
                ax.set_ylabel("Sim. hit r [mm]")
                ax.set_title(f"System {system}, layer {double_layers}")
                pdf.savefig()
                plt.close()


    def plot_doublet_efficiency_vs_sim(self, pdf: PdfPages):

        bins = {
            f"mcp_pt": np.linspace(0, 10, 201),
            f"mcp_eta": np.linspace(-0.7, 0.7, 281),
            f"mcp_phi": np.linspace(-3.2, 3.2, 321),
            (f"mcp_pt", f"mcp_phi"): [np.linspace(0, 10, 11),
                                      np.linspace(-3.2, 3.2, 1601)],
            (f"mcp_q_over_pt", f"mcp_eta"): [np.linspace(-1, 1, 201),
                                             np.linspace(-0.7, 0.7, 281)],
            (f"mcp_q_over_pt", f"mcp_phi"): [np.linspace(-1, 1, 201),
                                             np.linspace(-3.2, 3.2, 321)],
            (f"mcp_eta", f"mcp_phi"): [np.linspace(-0.7, 0.7, 281),
                                       np.linspace(-3.2, 3.2, 321)],
        }
        system_name = {
            INNER_TRACKER_BARREL: "Inner Tracker Barrel",
            OUTER_TRACKER_BARREL: "Outer Tracker Barrel",
        }
        xlabel = {
            "mcp_pt": "Simulated $p_T$ [GeV]",
            "mcp_eta": "Simulated eta",
            "mcp_phi": "Simulated phi [rad]",
            "mcp_q_over_pt": "Simulated $q/p_T$ [1/GeV]",
        }
        for system in SYSTEMS:
            for layer in LAYERS:
                abbrev = SYSTEM_ABBREV[system]
                n_modules = N_MODULES[system][layer]
                phi_interval = 2 * np.pi / (n_modules / self.n_phi_for_modulo)
                expectation = f"mcp_phi_mod_{abbrev}_{layer}"
                the_bins = np.linspace(0, phi_interval, 201)
                bins[expectation] = the_bins
                bins[ ("mcp_q_over_pt", expectation) ] = [np.linspace(-1, 1, 201), the_bins]
                bins[ ("mcp_eta", expectation) ] = [np.linspace(-0.7, 0.7, 281), the_bins]
                xlabel[expectation] = f"Simulated phi mod {phi_interval:.4f} [rad]"

        # mask for first exit / arc / path
        first_exit = first_exit_mask(self.df)

        # denominator of efficiency
        mask_denom = ~(self.df["simhit"].astype(bool))
        df_denom = self.df[mask_denom]
        if df_denom.duplicated().any():
            warnings.warn("Warning: duplicates found in denominator dataframe!")

        debug = False
        for kinematic in [
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
            # "mcp_phi_mod_ITB_0",
            # "mcp_phi_mod_ITB_2",
            # "mcp_phi_mod_ITB_4",
            # "mcp_phi_mod_ITB_6",
            ("mcp_q_over_pt", "mcp_eta"),
            ("mcp_q_over_pt", "mcp_phi"),
            ("mcp_eta", "mcp_phi"),
            ("mcp_eta", "mcp_phi_mod_ITB_0"),
            # ("mcp_eta", "mcp_phi_mod_ITB_2"),
            # ("mcp_eta", "mcp_phi_mod_ITB_4"),
            # ("mcp_eta", "mcp_phi_mod_ITB_6"),
            ("mcp_q_over_pt", "mcp_phi_mod_ITB_0"),
            # ("mcp_q_over_pt", "mcp_phi_mod_ITB_2"),
            # ("mcp_q_over_pt", "mcp_phi_mod_ITB_4"),
            # ("mcp_q_over_pt", "mcp_phi_mod_ITB_6"),
        ]:

            for system in SYSTEMS:

                for double_layers in [
                    [0, 1],
                    [2, 3],
                    [4, 5],
                    [6, 7],
                ]:
                    # check if 1d or 2d plots
                    is2d = isinstance(kinematic, tuple) and len(kinematic) == 2
                    abbrev = SYSTEM_ABBREV[system]

                    # special case: modded phi
                    expectation = f"mcp_phi_mod_{abbrev}_{double_layers[0]}"
                    if not is2d:
                        if kinematic.startswith("mcp_phi_mod") and kinematic != expectation:
                                continue
                    else:
                        ok = True
                        for dim in range(2):
                            if (kinematic[dim].startswith("mcp_phi_mod") and kinematic[dim] != expectation):
                                ok = False
                        if not ok:
                            continue

                    # announcement
                    print(f"Plotting sim hit doublet efficiency vs {kinematic} for system={system} double_layers={double_layers} ...")

                    # numerator
                    mask_numer = numerator_mask(self.df, [system], double_layers) & first_exit

                    # calculate doublet efficiency
                    # this is a lot of vector algebra
                    two_layers = 2
                    doublet_cols = [
                        "file",
                        "i_event", # the event
                        "i_mcp", # the MC particle
                        "simhit_system", # the system (IT, OT)
                        "simhit_layer_div_2", # the double layer
                        "simhit_module", # the phi-module
                        "simhit_sensor", # the z-sensor
                    ]
                    doublet_groups = self.df[mask_numer].groupby(doublet_cols)
                    valid_doublets = doublet_groups["simhit_layer"].nunique().ge(two_layers).reset_index(name="valid_doublet")

                    # determine if there is at least one valid doublet per group
                    doublet_layer_cols = [
                        "file",
                        "i_event",
                        "i_mcp",
                        "simhit_system",
                        "simhit_layer_div_2",
                    ]
                    at_least_one_doublet = (
                        valid_doublets
                        .groupby(doublet_layer_cols)["valid_doublet"]
                        .any()
                        .reset_index(name="at_least_one_doublet")
                    )

                    # get kinematic info of the first row in doublet
                    mcp_kin = (
                        self.df[mask_numer]
                        .groupby(doublet_layer_cols)[kinematic if not is2d else list(kinematic)]
                        .first()
                        .reset_index()
                    )

                    # merge kinematic info
                    at_least_one_doublet = at_least_one_doublet.merge(
                        mcp_kin,
                        on=doublet_layer_cols,
                        how="left",
                    )
                    df_numer = at_least_one_doublet[at_least_one_doublet["at_least_one_doublet"].astype(bool)]

                    # calculate efficiency
                    if is2d:
                        counts_denom, _, _ = np.histogram2d(
                            df_denom[kinematic[0]],
                            df_denom[kinematic[1]],
                            bins=bins[kinematic],
                        )
                        counts_numer, _, _ = np.histogram2d(
                            df_numer[kinematic[0]],
                            df_numer[kinematic[1]],
                            bins=bins[kinematic],
                        )
                        efficiency = np.divide(
                            counts_numer,
                            counts_denom,
                            out=np.full_like(counts_denom, 0.0, dtype=float),
                            where=(counts_denom > 0.0),
                        )

                        xedges, yedges = bins[kinematic]
                        fig, ax = plt.subplots(figsize=(8, 8))
                        mesh = ax.pcolormesh(
                            xedges,
                            yedges,
                            efficiency.T,
                            cmap="afmhot",
                            vmin=0.945,
                            vmax=1.005,
                        )
                        fig.colorbar(mesh, ax=ax, pad=0.01, label="Sim. hit double-layer efficiency")
                        ax.set_xlabel(xlabel[kinematic[0]])
                        ax.set_ylabel(xlabel[kinematic[1]])
                        ax.set_title(f"{system_name[system]}, layer {double_layers}")
                        pdf.savefig()
                        plt.close()

                    else:

                        # efficiency plots
                        counts_denom, _ = np.histogram(df_denom[kinematic], bins=bins[kinematic])
                        counts_numer, _ = np.histogram(df_numer[kinematic], bins=bins[kinematic])
                        efficiency = np.divide(
                            counts_numer,
                            counts_denom,
                            out=np.full_like(counts_denom, 0.0, dtype=float),
                            where=(counts_numer > 0.0),
                        )
                        bin_centers = (bins[kinematic][1:] + bins[kinematic][:-1]) / 2.0

                        for ylo, yhi in [
                            (0.86, 1.01),
                            # (0.6, 1.04),
                            # (0.945, 1.005),
                        ]:
                            fig, ax = plt.subplots(figsize=(8, 8))
                            ax.plot(
                                bin_centers,
                                efficiency,
                                marker="o",
                                markersize=2,
                                linestyle="-",
                                linewidth=1,
                                color="dodgerblue",
                            )
                            ax.set_xlabel(xlabel[kinematic])
                            ax.set_ylabel(f"Sim. hit double-layer efficiency")
                            ax.set_title(f"{system_name[system]}, layer {double_layers}")
                            ax.set_ylim(ylo, yhi)
                            if kinematic in ["mcp_eta", "mcp_phi"]:
                                bounds = get_boundaries(kinematic, [system], double_layers)
                                bounds = bounds[(bounds > min(bins[kinematic])) & (bounds < max(bins[kinematic]))]
                                max_eff = 1.0
                                arrowprops = dict(arrowstyle="->", color="red", lw=1)
                                kwargs = dict(xycoords="data", textcoords="data", arrowprops=arrowprops)
                                for i_bound, bound in enumerate(bounds):
                                    if i_bound == 0:
                                        ax.text(bound, (max_eff + yhi)/2.0, "Sensor boundaries", color="red", fontsize=10, ha="left", va="bottom")
                                    ax.annotate(text="", xy=(bound, max_eff), xytext=(bound, (max_eff + yhi)/2.0), **kwargs)
                            pdf.savefig()
                            plt.close()


def numerator_mask(
    df: pd.DataFrame,
    systems: list[int],
    layers: list[int],
) -> pd.Series:
    return (
        (df["i_mcp"] >= 0) &
        (df["simhit"].astype(bool)) &
        (df["simhit_system"].isin(systems)) &
        (df["simhit_layer"].isin(layers)) &
        (df["simhit_inside_bounds"].isin([INSIDE_BOUNDS,
                                          UNDEFINED_BOUNDS]))
    )


def first_exit_mask(df: pd.DataFrame) -> pd.Series:
    return (
        (df["simhit_costheta"] > MIN_COSTHETA) &
        (df["simhit_p"] / df["mcp_p"] > MIN_SIMHIT_PT_FRACTION) &
        (df["simhit_t_corrected"] < MAX_TIME)
    )


def get_boundaries(kinematic: str, systems: list[int], layers: list[int]) -> np.ndarray:
    if kinematic == "mcp_eta":
        return get_eta_boundaries(systems, layers)
    elif kinematic == "mcp_phi":
        return get_phi_boundaries(systems, layers)
    else:
        raise ValueError(f"Unknown kinematic for boundaries: {kinematic}")


def get_eta_boundaries(systems: list[int], layers: list[int]) -> np.ndarray:
    bounds = []
    for system in systems:
        for layer in layers:
            for i_sensor in range(N_SENSORS[system][layer] // 2):
                z = i_sensor * SENSOR_SIZE[system]
                r = RADIUS[system][layer]
                theta = np.arctan2(r, z)
                eta = -np.log(np.tan(theta / 2.0))
                bounds.append(eta)
                bounds.append(-eta)
    return np.array(list(sorted(set(bounds))))


def get_phi_boundaries(systems: list[int], layers: list[int]) -> np.ndarray:
    bounds = []
    for system in systems:
        for layer in layers:
            n_modules = N_MODULES[system][layer]
            for i_module in range(n_modules):
                phi = (2.0 * np.pi / n_modules) * (i_module + 0.5)
                if phi > np.pi:
                    phi -= 2.0 * np.pi
                bounds.append(phi)
    return np.array(list(sorted(set(bounds))))
