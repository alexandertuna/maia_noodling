import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

from constants import DET_IDS, DET_NAMES
EPSILON = 1e-3

class Plotter:

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.cmap = "turbo"
        df["hit_rt"] = np.sqrt(df["hit_x"]**2 + df["hit_y"]**2)
        df["hit_theta"] = np.arctan2(df["hit_rt"], df["hit_z"])
        df["hit_eta"] = -np.log(np.tan(df["hit_theta"] / 2))
        df["hit_phi"] = np.arctan2(df["hit_y"], df["hit_x"])


    def plot(self, pdf_name: str) -> None:
        print(f"Saving plots to {pdf_name} ...")
        with PdfPages(pdf_name) as pdf:
            self.plot_hit_eta_phi(pdf)
            self.plot_hit_module_layer(pdf)


    def plot_hit_eta_phi(self, pdf: PdfPages) -> None:
        print("Plotting hit eta phi ...")
        eta_bins = np.linspace(-3, 3, 100)
        phi_bins = np.linspace(-3.2, 3.2, 100)
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df["hit_eta"],
            self.df["hit_phi"],
            bins=[eta_bins, phi_bins],
            cmin=0.5,
            cmap=self.cmap,
        )
        fig.colorbar(im, ax=ax, label="Hits")
        ax.set_xlabel("Hit Eta")
        ax.set_ylabel("Hit Phi")
        ax.tick_params(axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()

        for det_id in DET_IDS:
            fig, ax = plt.subplots(figsize=(8,8))
            df = self.df[self.df["hit_system"] == det_id]
            _, _, _, im = ax.hist2d(
                df["hit_eta"],
                df["hit_phi"],
                bins=[eta_bins, phi_bins],
                cmin=0.5,
                cmap=self.cmap,
            )
            fig.colorbar(im, ax=ax, label="Hits")
            ax.set_title(DET_NAMES[det_id])
            ax.set_xlabel("Hit Eta")
            ax.set_ylabel("Hit Phi")
            ax.tick_params(axis="both", which="both", direction="in")
            fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            pdf.savefig()
            plt.close()


    def plot_hit_module_layer(self, pdf: PdfPages) -> None:
        module_bins = np.arange(-1.5, self.df["hit_module"].max() + 1.5 + EPSILON, 1)
        layer_bins = np.arange(-1.5, self.df["hit_layer"].max() + 1.5 + EPSILON, 1)

        for det_id in DET_IDS:
            print(f"Plotting hit module layer for {DET_NAMES[det_id]} ...")
            df = self.df[self.df["hit_system"] == det_id]
            fig, ax = plt.subplots(figsize=(8,8))
            _, _, _, im = ax.hist2d(
                df["hit_module"],
                df["hit_layer"],
                bins=[module_bins, layer_bins],
                cmin=0.5,
                cmap=self.cmap,
            )
            fig.colorbar(im, ax=ax, label="Hits")
            ax.set_title(DET_NAMES[det_id])
            ax.set_xlabel("Hit Module")
            ax.set_ylabel("Hit Layer")
            ax.tick_params(axis="both", which="both", direction="in")
            fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            pdf.savefig()
            plt.close()
