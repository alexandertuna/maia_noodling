import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

from constants import DET_IDS, DET_NAMES
EPSILON = 1e-3

class Plotter:

    def __init__(self, df: pd.DataFrame, mmdf: pd.DataFrame) -> None:
        self.df = df
        self.mmdf = mmdf
        self.cmap = "turbo"
        df["hit_rt"] = np.sqrt(df["hit_x"]**2 + df["hit_y"]**2)
        df["hit_theta"] = np.arctan2(df["hit_rt"], df["hit_z"])
        df["hit_eta"] = -np.log(np.tan(df["hit_theta"] / 2))
        df["hit_phi"] = np.arctan2(df["hit_y"], df["hit_x"])


    def plot(self, pdf_name: str) -> None:
        print(f"Saving plots to {pdf_name} ...")
        with PdfPages(pdf_name) as pdf:
            self.plot_hit_eta_phi(pdf)
            self.plot_hit_z(pdf)
            self.plot_hit_sensor(pdf)
            self.plot_hit_z_sensor(pdf)
            self.plot_hit_cellid1(pdf)
            self.plot_hit_module_layer(pdf)
            # self.plot_module_counts(pdf)
            self.plot_module_position(pdf)


    def plot_hit_eta_phi(self, pdf: PdfPages) -> None:
        print("Plotting hit eta phi ...")
        eta_bins = np.linspace(-3, 3, 100)
        phi_bins = np.linspace(-3.2, 3.2, 100)
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df["hit_eta"],
            self.df["hit_phi"],
            bins=[eta_bins, phi_bins],
            vmin=0,
            cmin=0.5,
            cmap=self.cmap,
        )
        fig.colorbar(im, ax=ax, label="Hits")
        ax.set_xlabel("Hit Eta")
        ax.set_ylabel("Hit Phi")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
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
                vmin=0,
                cmin=0.5,
                cmap=self.cmap,
            )
            fig.colorbar(im, ax=ax, label="Hits")
            ax.set_title(DET_NAMES[det_id])
            ax.set_xlabel("Hit Eta")
            ax.set_ylabel("Hit Phi")
            ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            pdf.savefig()
            plt.close()


    def plot_hit_z(self, pdf: PdfPages) -> None:
        print("Plotting hit z ...")
        bins = 100 # np.linspace(-300, 300, 100)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df["hit_z"], bins=bins, histtype="stepfilled", color="blue", alpha=0.7)
        ax.set_xlabel("Hit Z [mm]")
        ax.set_ylabel("Hits")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()


    def plot_hit_sensor(self, pdf: PdfPages) -> None:
        print("Plotting hit sensor ...")
        bins = 100 # np.linspace(-300, 300, 100)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df["hit_sensor"], bins=bins, histtype="stepfilled", color="blue", alpha=0.7)
        ax.set_xlabel("Hit sensor [mm]")
        ax.set_ylabel("Hits")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()


    def plot_hit_z_sensor(self, pdf: PdfPages) -> None:
        print("Plotting hit z sensor ...")
        # eta_bins = np.linspace(-3, 3, 100)
        # phi_bins = np.linspace(-3.2, 3.2, 100)
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df["hit_z"],
            self.df["hit_sensor"],
            bins=[100, 100],
            vmin=0,
            cmin=0.5,
            cmap=self.cmap,
        )
        fig.colorbar(im, ax=ax, label="Hits")
        ax.set_xlabel("Hit Z")
        ax.set_ylabel("Hit Sensor")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()


    def plot_hit_cellid1(self, pdf: PdfPages) -> None:
        print("Plotting hit cellid1 ...")
        bins = 100 # np.linspace(-300, 300, 100)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df["hit_cellid1"], bins=bins, histtype="stepfilled", color="blue", alpha=0.7)
        ax.set_xlabel("Hit cellid1 [mm]")
        ax.set_ylabel("Hits")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
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
                vmin=0,
                cmin=0.5,
                cmap=self.cmap,
            )
            fig.colorbar(im, ax=ax, label="Hits")
            ax.set_title(DET_NAMES[det_id])
            ax.set_xlabel("Hit Module")
            ax.set_ylabel("Hit Layer")
            ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            pdf.savefig()
            plt.close()

    def plot_module_counts(self, pdf: PdfPages) -> None:
        """
        For interpretation purposes, this is mostly for barrel only
        """
        print("Plotting module counts ...")
        max_counts = self.mmdf["count"].max()
        bins = np.arange(0, max_counts, int(max_counts/1000)+1)

        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(
            self.mmdf["count"],
            bins=bins,
            histtype="stepfilled",
            color="blue",
            alpha=0.7,
            )
        ax.set_xlabel("Number of next-module counts")
        ax.set_ylabel("Counts")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        ax.semilogy()
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()

        # make interesting combinations of requirements to suss out peaks
        #####
        #####
        #####


    def plot_module_position(self, pdf: PdfPages) -> None:
        print("Plotting module positions ...")
        bins = [
            np.linspace(125, 175, 200),
            np.linspace(-19, 19, 200),
        ]

        layer, module, side, system, sensor = 0, 0, 0, 3, 0  # barrel example

        mask = (
            (self.mmdf["hit_layer"] == layer) &
            (self.mmdf["hit_module"] == module) &
            (self.mmdf["hit_side"] == side) &
            (self.mmdf["hit_system"] == system) &
            (self.mmdf["hit_sensor"] == sensor)
        )

        for hit in ["hit", "next_hit"]:
            fig, ax = plt.subplots(figsize=(8,8))
            _, _, _, im = ax.hist2d(
                self.mmdf[mask][f"{hit}_x"],
                self.mmdf[mask][f"{hit}_y"],
                # pd.concat([self.mmdf[mask]["hit_x"], self.mmdf[mask]["next_hit_x"]]),
                # pd.concat([self.mmdf[mask]["hit_y"], self.mmdf[mask]["next_hit_y"]]),
                bins=bins,
                vmin=0,
                cmin=0.5,
                cmap=self.cmap,
                )
            fig.colorbar(im, ax=ax, label="Next-module counts")
            ax.set_title(f"System {system} Side {side} Layer {layer} Module {module}")
            ax.set_xlabel("Hit X [mm]")
            ax.set_ylabel("Hit Y [mm]")
            ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            pdf.savefig()
            plt.close()


