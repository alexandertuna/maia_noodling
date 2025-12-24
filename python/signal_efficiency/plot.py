import warnings
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

INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5
SYSTEMS = [
    INNER_TRACKER_BARREL,
    OUTER_TRACKER_BARREL,
]
LAYERS = range(8)
MAX_TIME = 3.0 # ns


class Plotter:


    def __init__(self, df: pd.DataFrame, pdf: str, inside_bounds: bool):
        self.df = df
        self.pdf = pdf
        self.inside_bounds = inside_bounds


    def plot(self):
        with PdfPages(self.pdf) as pdf:
            self.title_slide(pdf)
            self.plot_mcp_pt(pdf)
            self.plot_mcp_eta(pdf)
            self.plot_mcp_phi(pdf)
            self.plot_simhit_time(pdf)
            self.plot_simhit_time_corrected(pdf)
            # self.plot_simhit_distance(pdf)
            self.plot_simhit_xy(pdf)
            self.plot_simhit_rz(pdf)
            self.plot_simhit_p(pdf)
            self.plot_simhit_pt(pdf)
            self.plot_simhit_costheta(pdf)
            self.plot_simhit_costheta_vs_time(pdf)
            self.plot_simhit_p_vs_time(pdf)
            self.plot_simhit_p_vs_costheta(pdf)
            self.plot_efficiency_vs_sim(pdf)
            # self.plot_weird_radius_hits(pdf)


    def title_slide(self, pdf: PdfPages):
        text = "Efficiency denominator"
        texts = [
            f" * Simulated muon gun, $p_T$ 0-10 GeV, $|\\eta| < {BARREL_TRACKER_MAX_ETA}$",
            f" * non-zero charge",
            f" * $p_T$ > {ONE_GEV} GeV",
            f" * Vertex r < {ONE_MM} mm",
            f" * abs(Vertex z) < {ONE_MM} mm",
            f" * Endpoint r > {BARREL_TRACKER_MAX_RADIUS} mm",
            f" * abs($\\eta$) < {BARREL_TRACKER_MAX_ETA}",
        ]
        dy = 0.05
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.1, 0.8, text, ha="left")
        for it, text in enumerate(texts):
            ax.text(0.1, 0.6 - it*dy, text, ha="left")
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
                ax.set_axisbelow(True)

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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
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
            ax.set_axisbelow(True)
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
            ax.set_axisbelow(True)
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
        ax.set_axisbelow(True)
        pdf.savefig()
        plt.close()


    def plot_efficiency_vs_sim(self, pdf: PdfPages):
        bins = {
            "mcp_pt": np.linspace(0, 10, 101),
            "mcp_eta": np.linspace(-0.8, 0.8, 161),
            "mcp_phi": np.linspace(-3.2, 3.2, 161),
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

        # text describing efficiency calculation
        dy = 0.05
        text = f"Efficiency numerator:"
        texts = [
            f"Number of MC particles with",
            f"at least 1 sim. hit on a layer which are",
            f" * Linked to the MC particle",
            f" * $t - R/c$ < {MAX_TIME} ns",
            f" * Inside the bounds of a sensor" if self.inside_bounds else "",
        ]
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.1, 0.8, text, ha="left")
        for it, text in enumerate(texts):
            ax.text(0.1, 0.6 - it*dy, text, ha="left")
        ax.axis("off")
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
        ]:

            print(f"Plotting sim hit efficiency vs {kinematic}...")
            for system in SYSTEMS:

                for layer in LAYERS:

                    mask_numer = (
                        (self.df["simhit"].astype(bool)) &
                        (self.df["simhit_system"] == system) &
                        (self.df["simhit_layer"] == layer) &
                        (self.df["simhit_t_corrected"] < MAX_TIME)
                    )

                    # dont double-count if >1 hits on a layer
                    subset = ["file", "i_event", "i_mcp", "simhit_system", "simhit_layer"]
                    df_numer = self.df[mask_numer].drop_duplicates(subset=subset)
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
                        linestyle="none",
                        color="dodgerblue",
                    )
                    ax.set_ylim(0.95, 1.005)
                    ax.set_xlabel(xlabel[kinematic])
                    ax.set_ylabel(f"Sim. hit efficiency with $t_{{corrected}}$ < {MAX_TIME} ns")
                    ax.set_title(f"{system_name[system]}, layer {layer}")
                    ax.set_axisbelow(True)
                    fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                    pdf.savefig()
                    plt.close()

