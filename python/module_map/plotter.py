import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

from constants import DET_IDS, DET_NAMES
EPSILON = 1e-3

class Plotter:

    def __init__(self,
                 df: pd.DataFrame,
                 sorted_df: pd.DataFrame,
                 mmdf: pd.DataFrame) -> None:
        self.df = df
        self.sorted_df = sorted_df
        self.mmdf = mmdf
        self.cmap = "turbo"
        df["hit_eta"] = -np.log(np.tan(df["hit_theta"] / 2))


    def plot(self, pdf_name: str) -> None:
        print(f"Saving plots to {pdf_name} ...")
        with PdfPages(pdf_name) as pdf:
            #### self.plot_hit_eta_phi(pdf)
            #### self.plot_hit_z(pdf)
            self.plot_hit_t(pdf)
            self.plot_hit_t_R(pdf)
            self.plot_hit_quality(pdf)
            #### self.plot_hit_sensor(pdf)
            #### self.plot_hit_z_sensor(pdf)
            self.plot_hit_module_layer(pdf)
            self.plot_hit_sensor_layer(pdf)
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


    def plot_hit_t(self, pdf: PdfPages) -> None:
        print("Plotting hit t ...")
        bins = np.linspace(-25, 125, 150)

        # hit_t
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df["hit_t"], bins=bins, histtype="stepfilled", color="blue")
        ax.set_xlabel("Hit time [ns]")
        ax.set_ylabel("Hits")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()

        # hit_t_corrected
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df["hit_t_corrected"], bins=bins, histtype="stepfilled", color="blue")
        ax.set_xlabel("Hit time (corrected) [ns]")
        ax.set_ylabel("Hits")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()


    def plot_hit_t_R(self, pdf: PdfPages) -> None:
        print("Plotting hit t vs R ...")
        # eta_bins = np.linspace(-3, 3, 100)
        # phi_bins = np.linspace(-3.2, 3.2, 100)
        bins = [
            np.linspace(-2, 20, 150),
            np.linspace(0, 2000, 100),
        ]
        fig, ax = plt.subplots(figsize=(8,8))
        _, _, _, im = ax.hist2d(
            self.df["hit_t"],
            self.df["hit_R"],
            bins=bins,
            vmin=0,
            cmin=0.5,
            cmap=self.cmap,
        )
        fig.colorbar(im, ax=ax, label="Hits")
        ax.set_xlabel("Hit time [ns]")
        ax.set_ylabel("Hit R [mm]")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()


    def plot_hit_quality(self, pdf: PdfPages) -> None:
        print("Plotting hit quality ...")
        bins = 100 # np.linspace(-25, 125, 150)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df["hit_quality"], bins=bins, histtype="stepfilled", color="blue")
        ax.set_xlabel("Hit quality")
        ax.set_ylabel("Hits")
        ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
        fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
        pdf.savefig()
        ax.semilogy()
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


    def plot_hit_sensor_layer(self, pdf: PdfPages) -> None:
        sensor_bins = np.arange(-1.5, self.df["hit_sensor"].max() + 1.5 + EPSILON, 1)
        layer_bins = np.arange(-1.5, self.df["hit_layer"].max() + 1.5 + EPSILON, 1)

        for det_id in DET_IDS:
            print(f"Plotting hit sensor layer for {DET_NAMES[det_id]} ...")
            df = self.df[self.df["hit_system"] == det_id]
            fig, ax = plt.subplots(figsize=(8,8))
            _, _, _, im = ax.hist2d(
                df["hit_sensor"],
                df["hit_layer"],
                bins=[sensor_bins, layer_bins],
                vmin=0,
                cmin=0.5,
                cmap=self.cmap,
            )
            fig.colorbar(im, ax=ax, label="Hits")
            ax.set_title(DET_NAMES[det_id])
            ax.set_xlabel("Hit sensor")
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

        layer, module, side, system = 3, 0, 0, 5  # barrel example
        mask_layer_module_side_system = (
                (self.sorted_df["hit_layer"] == layer) &
                (self.sorted_df["hit_module"] == module) &
                (self.sorted_df["hit_side"] == side) &
                (self.sorted_df["hit_system"] == system)
            )

        # for sensor in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        for sensor in range(15, 25):
            print(f"Plotting System {system} Side {side} Layer {layer} Module {module} Sensor {sensor} ...")

            mask = mask_layer_module_side_system & (self.sorted_df["hit_sensor"] == sensor)
            if not mask.any():
                print(f"  No hits for System {system} Side {side} Layer {layer} Module {module} Sensor {sensor}, skipping ...")
                continue

            # # xy
            # all_x = pd.concat([self.sorted_df[mask]["hit_x"], self.sorted_df[mask]["next_hit_x"]])
            # all_y = pd.concat([self.sorted_df[mask]["hit_y"], self.sorted_df[mask]["next_hit_y"]])
            # xlim = (all_x.min() - 5, all_x.max() + 5)
            # ylim = (all_y.min() - 5, all_y.max() + 5)
            # bins = [
            #     np.linspace(xlim[0], xlim[1], 200),
            #     np.linspace(ylim[0], ylim[1], 200),
            # ]

            # # hist2d
            # for hit in ["hit", "next_hit"]:
            #     fig, ax = plt.subplots(figsize=(8,8))
            #     _, _, _, im = ax.hist2d(
            #         self.sorted_df[mask][f"{hit}_x"],
            #         self.sorted_df[mask][f"{hit}_y"],
            #         bins=bins,
            #         vmin=0,
            #         cmin=0.5,
            #         cmap=self.cmap,
            #         )
            #     fig.colorbar(im, ax=ax, label="Next-module counts")
            #     ax.set_title(f"System {system} Side {side} Layer {layer} Module {module} Sensor {sensor}")
            #     ax.set_xlabel("Hit x [mm]")
            #     ax.set_ylabel("Hit y [mm]")
            #     ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            #     fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            #     pdf.savefig()
            #     plt.close()

            # # 2x scatter
            # fig, ax = plt.subplots(figsize=(8,8))
            # ax.scatter(self.sorted_df[mask][f"hit_x"],
            #            self.sorted_df[mask][f"hit_y"],
            #            c="blue",
            #            s=1,
            #            )
            # ax.scatter(self.sorted_df[mask][f"next_hit_x"],
            #            self.sorted_df[mask][f"next_hit_y"],
            #            c="red",
            #            s=1,
            #            )
            # ax.set_title(f"System {system} Side {side} Layer {layer} Module {module} Sensor {sensor}")
            # ax.set_xlabel("Hit x [mm]")
            # ax.set_ylabel("Hit y [mm]")
            # ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            # fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            # pdf.savefig()
            # plt.close()

            # # rz
            # all_r = pd.concat([self.sorted_df[mask]["hit_r"], self.sorted_df[mask]["next_hit_r"]])
            # all_z = pd.concat([self.sorted_df[mask]["hit_z"], self.sorted_df[mask]["next_hit_z"]])
            # rlim = (all_r.min() - 5, all_r.max() + 5)
            # zlim = (all_z.min() - 5, all_z.max() + 5)
            # bins = [
            #     np.linspace(zlim[0], zlim[1], 200),
            #     np.linspace(rlim[0], rlim[1], 200),
            # ]

            # for hit in ["hit", "next_hit"]:
            #     fig, ax = plt.subplots(figsize=(8,8))
            #     _, _, _, im = ax.hist2d(
            #         self.sorted_df[mask][f"{hit}_z"],
            #         self.sorted_df[mask][f"{hit}_r"],
            #         bins=bins,
            #         vmin=0,
            #         cmin=0.5,
            #         cmap=self.cmap,
            #         )
            #     fig.colorbar(im, ax=ax, label="Next-module counts")
            #     ax.set_title(f"System {system} Side {side} Layer {layer} Module {module} Sensor {sensor}")
            #     ax.set_xlabel("Hit z [mm]")
            #     ax.set_ylabel("Hit r [mm]")
            #     ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            #     fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            #     pdf.savefig()
            #     plt.close()

            # # 2x scatter
            # fig, ax = plt.subplots(figsize=(8,8))
            # ax.scatter(self.sorted_df[mask][f"hit_z"],
            #            self.sorted_df[mask][f"hit_r"],
            #            c="blue",
            #            s=1,
            #            )
            # ax.scatter(self.sorted_df[mask][f"next_hit_z"],
            #            self.sorted_df[mask][f"next_hit_r"],
            #            c="red",
            #            s=1,
            #            )
            # ax.set_title(f"{system=} {side=} {layer=} {module=} {sensor=}")
            # ax.set_xlabel("Hit z [mm]")
            # ax.set_ylabel("Hit r [mm]")
            # ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            # fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            # pdf.savefig()
            # plt.close()


            def format_title(system: int, side: int, layer: int, module: int, sensor: int) -> str:
                if system not in [3, 5]:
                    raise ValueError("Only ITB (system 3) and OTB (system 5) supported")
                _system = "ITB" if system == 3 else "OTB"
                if _system in ["ITB", "OTB"]:
                    if side != 0:
                        raise ValueError("ITB/OTB only has side 0")
                else:
                    _side = "A" if side == 1 else "C"
                    _system = f"{_system}, {_side}"
                _layer = f"L{layer:02d}"
                _module = f"φ{module:02d}"
                _sensor = f"θ{sensor:03d}"
                return f"{_system} {_layer} {_module} {_sensor}"


            # phi theta
            all_theta = pd.concat([self.sorted_df[mask]["hit_theta"], self.sorted_df[mask]["next_hit_theta"]])
            all_phi = pd.concat([self.sorted_df[mask]["hit_phi"], self.sorted_df[mask]["next_hit_phi"]])
            theta_lim = [all_theta.min() - 0.01,
                         all_theta.max() + 0.03]
            phi_lim = [all_phi.min() - 0.01,
                       all_phi.max() + 0.01]
            # bins = [
            #     np.linspace(philim[0], philim[1], 200),
            #     np.linspace(thetalim[0], thetalim[1], 200),
            # ]
            # for hit in ["hit", "next_hit"]:
            #     fig, ax = plt.subplots(figsize=(8,8))
            #     _, _, _, im = ax.hist2d(
            #         self.sorted_df[mask][f"{hit}_theta"],
            #         self.sorted_df[mask][f"{hit}_phi"],
            #         bins=bins,
            #         vmin=0,
            #         cmin=0.5,
            #         cmap=self.cmap,
            #         )
            #     fig.colorbar(im, ax=ax, label="Next-module counts")
            #     ax.set_title(f"System {system} Side {side} Layer {layer} Module {module} Sensor {sensor}")
            #     ax.set_xlabel("Hit theta [rad]")
            #     ax.set_ylabel("Hit phi [rad]")
            #     ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            #     fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            #     pdf.savefig()
            #     plt.close()


            # 2x scatter
            fig, ax = plt.subplots(figsize=(8,8))
            # ax.scatter(self.sorted_df[mask][f"hit_phi"],
            #            self.sorted_df[mask][f"hit_theta"],
            #            c="black",
            #            s=10,
            #            )
            # ax.scatter(self.sorted_df[mask][f"next_hit_theta"],
            #            self.sorted_df[mask][f"next_hit_phi"],
            #            c="red",
            #            s=10,
            #            )

            # Draw bounding box of hit_theta, hit_phi
            quantile = [0.001, 0.999]
            theta_min, theta_max = self.sorted_df[mask]["hit_theta"].quantile(quantile)
            phi_min, phi_max = self.sorted_df[mask]["hit_phi"].quantile(quantile)

            # theta_min = self.sorted_df[mask]["hit_theta"].min()
            # theta_max = self.sorted_df[mask]["hit_theta"].max()
            # phi_min = self.sorted_df[mask]["hit_phi"].min()
            # phi_max = self.sorted_df[mask]["hit_phi"].max()

            ax.plot([phi_min, phi_min, phi_max, phi_max, phi_min],
                    [theta_min, theta_max, theta_max, theta_min, theta_min],
                    color="black",
                    linestyle="-",
                    # label="Hit bounding box",
                    )

            total = len(self.sorted_df[mask])

            columns = [
                "next_hit_system",
                "next_hit_side",
                "next_hit_layer",
                "next_hit_module",
                "next_hit_sensor",
            ]

            # groupby, but sorted by number of rows of group
            grouped = self.sorted_df[mask].groupby(columns)
            grouped = sorted(grouped, key=lambda x: len(x[1]), reverse=True)
            for (system_, side_, layer_, module_, sensor_), group in grouped:
                frac = len(group) / total
                title = format_title(system_, side_, layer_, module_, sensor_)
                print(f"  Plotting next hit group {(system_, side_, layer_, module_, sensor_)} with {len(group)} hits ...")
                ax.scatter(group["next_hit_phi"],
                           group["next_hit_theta"],
                           label=f"{title} ({frac:.1%})",
                           s=10,
                           )
                # debug
                if True:
                    # mask_ = (group["next_hit_theta"] < theta_min) | (group["next_hit_theta"] > theta_max) | (group["next_hit_theta"] > (theta_max - 0.01)) | (group["next_hit_theta"] < (theta_min + 0.01))
                    mask_ = ((group["next_hit_theta"] > 1.17) & (group["next_hit_theta"] < 1.18))
                    if mask_.any():
                        with pd.option_context("display.min_rows", 50,
                                               "display.max_rows", 50,
                                            ):
                            print(group[mask_][[
                                "hit_t",
                                "next_hit_theta",
                                "next_hit_phi",
                                "next_hit_module",
                                "next_hit_sensor",
                                "next_hit_t",
                            ]])
            ncols = 1 + (len(grouped) // 3)
            ax.legend(markerscale=3, fontsize=8, ncols=ncols, loc="upper center")

            ax.set_xlim(phi_lim)
            ax.set_ylim(theta_lim)

            title = format_title(system, side, layer, module, sensor)
            ax.set_title(f'{title} (φ = "module", θ = "sensor")')
            ax.set_xlabel("Hit phi")
            ax.set_ylabel("Hit theta")
            ax.tick_params(right=True, top=True, axis="both", which="both", direction="in")
            fig.subplots_adjust(bottom=0.12, left=0.15, right=0.95, top=0.95)
            pdf.savefig()
            plt.close()



