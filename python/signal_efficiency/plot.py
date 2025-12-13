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
        system, layer, max_time = 3, 0, 3  # IT barrel layer 0
        bins = np.linspace(-1.2, 1.2, 121)
        mask_denom = ~self.df["hit"].astype(bool)
        mask_numer = (
            (self.df["hit"].astype(bool)) &
            (self.df["hit_system"] == system) &
            (self.df["hit_layer"] == layer) &
            (self.df["hit_t_corrected"] < max_time)
        )
        # dont double-count if >1 hits on a layer
        subset = ["file", "i_event", "i_sim", "hit_system", "hit_layer"]
        df_denom = self.df[mask_denom]
        df_numer = self.df[mask_numer].drop_duplicates(subset=subset)
        counts_denom, _ = np.histogram(df_denom["sim_eta"], bins=bins)
        counts_numer, _ = np.histogram(df_numer["sim_eta"], bins=bins)
        efficiency = np.divide(
            counts_numer,
            counts_denom,
            out=np.full_like(counts_denom, 0.0, dtype=float),
            where=(counts_numer > 0.0),
        )
        bin_centers = (bins[1:] + bins[:-1]) / 2.0
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.plot(bin_centers,
                efficiency,
                marker="o",
                linestyle="none",
                color="dodgerblue",
                )
        ax.set_ylim(0.8, 1.02)
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Simulated eta")
        ax.set_ylabel("Hit Efficiency")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()

