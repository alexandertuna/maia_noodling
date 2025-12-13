import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

class Plotter:


    def __init__(self, df: pd.DataFrame, pdf: str):
        self.df = df
        self.pdf = pdf


    def plot(self):
        with PdfPages(self.pdf) as pdf:
            self.plot_sim_pt(pdf)
            self.plot_sim_eta(pdf)
            self.plot_sim_phi(pdf)
            self.plot_hit_time(pdf)
            self.plot_hit_time_corrected(pdf)
            self.plot_efficiency_vs_sim_eta(pdf)


    def plot_sim_pt(self, pdf: PdfPages):
        mask = ~(self.df["hit"].astype(bool))
        bins = np.linspace(0, 10, 101)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["sim_pt"],
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


    def plot_sim_eta(self, pdf: PdfPages):
        mask = ~(self.df["hit"].astype(bool))
        bins = np.linspace(-1.2, 1.2, 101)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["sim_eta"],
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


    def plot_sim_phi(self, pdf: PdfPages):
        mask = ~(self.df["hit"].astype(bool))
        bins = np.linspace(-3.2, 3.2, 161)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["sim_phi"],
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
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Sim. hit time, corrected for propagation [ns]")
        ax.set_ylabel("Counts")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_efficiency_vs_sim_eta(self, pdf: PdfPages):
        bins = {
            "sim_pt": np.linspace(0, 10, 101),
            "sim_eta": np.linspace(-1.0, 1.0, 101),
            "sim_phi": np.linspace(-3.2, 3.2, 161),
        }
        system_name = {
            3: "Inner Tracker Barrel",
            5: "Outer Tracker Endcap",
        }
        max_time = 3.0 # ns

        # denominator of efficiency
        mask_denom = ~(self.df["hit"].astype(bool))
        df_denom = self.df[mask_denom]
        if df_denom.duplicated().any():
            warnings.warn("Warning: duplicates found in denominator dataframe!")

        for kinematic in [
            "sim_pt",
            "sim_eta",
            "sim_phi",
        ]:

            # system, layer, max_time = 3, 0, 3  # IT barrel layer 0
            print(f"Plotting hit efficiency vs {kinematic}...")

            for system in [3, 5]:

                for layer in [0, 1, 2, 3, 4, 5, 6, 7]:

                    mask_numer = (
                        (self.df["hit"].astype(bool)) &
                        (self.df["hit_system"] == system) &
                        (self.df["hit_layer"] == layer) &
                        (self.df["hit_t_corrected"] < max_time)
                    )

                    # dont double-count if >1 hits on a layer
                    subset = ["file", "i_event", "i_sim", "hit_system", "hit_layer"]
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
                    ax.set_ylim(0.8, 1.02)
                    ax.tick_params(direction="in", which="both", top=True, right=True)
                    ax.set_xlabel(kinematic)
                    ax.set_ylabel(f"Hit efficiency with $t_{{corrected}}$ < {max_time} ns")
                    ax.set_title(f"{system_name[system]}, layer {layer}")
                    ax.minorticks_on()
                    ax.grid(which="both")
                    ax.set_axisbelow(True)
                    fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                    pdf.savefig()
                    plt.close()

