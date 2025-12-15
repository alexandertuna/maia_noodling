import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5
SYSTEMS = [
    INNER_TRACKER_BARREL,
    OUTER_TRACKER_BARREL,
]
LAYERS = range(8)
MAX_TIME = 3.0 # ns


class Plotter:


    def __init__(self, df: pd.DataFrame, pdf: str):
        self.df = df
        self.pdf = pdf


    def plot(self):
        with PdfPages(self.pdf) as pdf:
            self.plot_mcp_pt(pdf)
            self.plot_mcp_eta(pdf)
            self.plot_mcp_phi(pdf)
            self.plot_hit_time(pdf)
            self.plot_hit_time_corrected(pdf)
            self.plot_hit_distance(pdf)
            self.plot_hit_xy(pdf)
            self.plot_hit_rz(pdf)
            self.plot_efficiency_vs_sim(pdf)



    def plot_mcp_pt(self, pdf: PdfPages):
        mask = ~(self.df["hit"].astype(bool))
        bins = np.linspace(0, 10, 101)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["mcp_pt"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Simulated $p_T$ [GeV]")
        ax.set_ylabel("Counts")
        ax.set_title("Simulated muon gun, $p_T$ 0-10 GeV")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_mcp_eta(self, pdf: PdfPages):
        mask = ~(self.df["hit"].astype(bool))
        bins = np.linspace(-0.9, 0.9, 181)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["mcp_eta"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Simulated eta")
        ax.set_ylabel("Counts")
        ax.set_title("Simulated muon gun, $p_T$ 0-10 GeV")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_mcp_phi(self, pdf: PdfPages):
        mask = ~(self.df["hit"].astype(bool))
        bins = np.linspace(-3.2, 3.2, 161)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["mcp_phi"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Simulated phi")
        ax.set_ylabel("Counts")
        ax.set_title("Simulated muon gun, $p_T$ 0-10 GeV")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_hit_time(self, pdf: PdfPages):
        mask = self.df["hit"].astype(bool)
        bins = np.linspace(0, 40, 201)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["hit_t"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                label="All hits",
                )
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Sim. hit time [ns]")
        ax.set_ylabel("Counts")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_hit_time_corrected(self, pdf: PdfPages):
        mask = self.df["hit"].astype(bool)
        bins = np.linspace(0, 40, 201)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["hit_t_corrected"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                label="All hits",
                )
        # add vertical line at MAX_TIME
        ax.axvline(MAX_TIME, color="red", linestyle="--")
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Sim. hit time, corrected for propagation [ns]")
        ax.set_ylabel("Counts")
        ax.set_title(f"Require sim. hit time < {MAX_TIME}ns")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_hit_distance(self, pdf: PdfPages):
        mask = self.df["hit"].astype(bool)
        bins = np.linspace(-300, 300, 301)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["hit_distance"],
                bins=bins,
                histtype="stepfilled",
                color="dodgerblue",
                alpha=0.9,
                )
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Sim. hit distance to surface [mm]")
        ax.set_ylabel("Counts")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_hit_xy(self, pdf: PdfPages):
        mask = self.df["hit"].astype(bool)
        bins = [
            np.linspace(-1500, 1500, 451),
            np.linspace(-1500, 1500, 451),
        ]
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df[mask]["hit_r"] * np.cos(self.df[mask]["hit_phi"]),
            self.df[mask]["hit_r"] * np.sin(self.df[mask]["hit_phi"]),
            bins=bins,
            cmap="gist_rainbow",
            cmin=0.5,
        )
        fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Sim. hit x [mm]")
        ax.set_ylabel("Sim. hit y [mm]")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.93, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_hit_rz(self, pdf: PdfPages):
        mask = self.df["hit"].astype(bool)
        bins = [
            np.linspace(-2000, 2000, 401),
            np.linspace(0, 1500, 451),
        ]
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df[mask]["hit_z"],
            self.df[mask]["hit_r"],
            bins=bins,
            cmap="gist_rainbow",
            cmin=0.5,
        )
        fig.colorbar(im, ax=ax, pad=0.01, label="Sim. hits")
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Sim. hit z [mm]")
        ax.set_ylabel("Sim. hit r [mm]")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.93, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


    def plot_efficiency_vs_sim(self, pdf: PdfPages):
        bins = {
            "mcp_pt": np.linspace(0, 10, 101),
            "mcp_eta": np.linspace(-0.9, 0.9, 91),
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

        # denominator of efficiency
        mask_denom = ~(self.df["hit"].astype(bool))
        df_denom = self.df[mask_denom]
        if df_denom.duplicated().any():
            warnings.warn("Warning: duplicates found in denominator dataframe!")

        for kinematic in [
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
        ]:

            print(f"Plotting hit efficiency vs {kinematic}...")
            for system in SYSTEMS:

                for layer in LAYERS:

                    mask_numer = (
                        (self.df["hit"].astype(bool)) &
                        (self.df["hit_system"] == system) &
                        (self.df["hit_layer"] == layer) &
                        (self.df["hit_t_corrected"] < MAX_TIME)
                    )

                    # dont double-count if >1 hits on a layer
                    subset = ["file", "i_event", "i_mcp", "hit_system", "hit_layer"]
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
                    ax.set_ylim(0.9, 1.01)
                    ax.tick_params(direction="in", which="both", top=True, right=True)
                    ax.set_xlabel(xlabel[kinematic])
                    ax.set_ylabel(f"Hit efficiency with $t_{{corrected}}$ < {MAX_TIME} ns")
                    ax.set_title(f"{system_name[system]}, layer {layer}")
                    ax.minorticks_on()
                    ax.grid(which="both")
                    ax.set_axisbelow(True)
                    fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                    pdf.savefig()
                    plt.close()

