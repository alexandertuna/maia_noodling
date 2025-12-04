import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

from constants import BARREL_RADII
from constants import SIDE, LAYERS, SENSORS, MODULES

class Plotter:

    def __init__(self, df: pd.DataFrame, pdf_path: str):
        self.df = df
        self.pdf_path = pdf_path
        self.signal = "sig" in pdf_path.lower()

        self.df["module_angle"] = self.df["hit_module"] * (2.0 * np.pi / len(MODULES))
        self.df["hit_xp"] = self.df["hit_x"] * np.cos(-1 * self.df["module_angle"]) - self.df["hit_y"] * np.sin(-1 * self.df["module_angle"])
        self.df["hit_yp"] = self.df["hit_x"] * np.sin(-1 * self.df["module_angle"]) + self.df["hit_y"] * np.cos(-1 * self.df["module_angle"])


    def plot(self):
        with PdfPages(self.pdf_path) as pdf:
            # self.plot_xy(pdf)
            # self.plot_rz(pdf, first_event=True)
            # if self.signal:
            #     self.plot_rz(pdf, first_event=False)
            self.plot_rz_events(pdf)


    def plot_xy(self, pdf: PdfPages, first_event: bool = False):
        if first_event:
            files = self.df["file"].unique()
            mask_first_event = (self.df["i_event"] == 0) & (self.df["file"] == files[0])
        for module in MODULES:
            mask = self.df["hit_module"] == module
            if first_event:
                mask &= mask_first_event
            df_module = self.df[mask]
            if len(df_module) == 0:
                continue
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.scatter(df_module["hit_x"], df_module["hit_y"], s=10)
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("y (mm)")
            ax.set_title(f"x vs y of Hits - Module {module}")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.1)
            pdf.savefig()
            plt.close()


    def plot_rz(self, pdf: PdfPages, first_event: bool):
        if first_event:
            files = self.df["file"].unique()
            mask_first_event = (self.df["i_event"] == 0) & (self.df["file"] == files[0])
        for sensor in SENSORS:
            for module in MODULES:
                print(f"Plotting module {module} ... rz")
                mask = (self.df["hit_module"] == module) & (self.df["hit_sensor"] == sensor)
                if first_event:
                    xlim = [self.df[mask]["hit_z"].min(),
                            self.df[mask]["hit_z"].max()]
                    mask &= mask_first_event
                df_module = self.df[mask]
                if len(df_module) == 0:
                    continue
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.scatter(df_module["hit_z"], df_module["hit_xp"], s=50)
                ax.set_xlabel("z (mm)")
                ax.set_ylabel("x (local) (mm)")
                # ax.set_xlim([-825, -770])
                # ax.set_ylim([816, 840])
                if first_event:
                    ax.set_title(f"Hits on module {module}, sensor {sensor}, event 0")
                    ax.set_xlim(xlim)
                else:
                    ax.set_title(f"Hits on module {module}, sensor {sensor}")
                ax.tick_params(direction="in", which="both", top=True, right=True)
                fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
                pdf.savefig()
                plt.close()


    def plot_rz_events(self, pdf: PdfPages):

        rzangles = []
        xyangles = []
        ptvalues = []
        zprojs = []
        yprojs = []
        n_debug = 0

        print("Finding rz, xy angles and projections ...")
        for i_group, ((sensor, module, filename, i_event, i_sim), group) in enumerate(self.df.groupby(["hit_sensor",
                                                                                                       "hit_module",
                                                                                                        "file",
                                                                                                        "i_event",
                                                                                                        "i_sim",
                                                                                                        ])):

            if len(group) == 0:
                continue
            if i_group % 100 == 0:
                print(f"Processing module {module}, sensor {sensor}, file {filename}, event {i_event} ...")
            # print(f"Plotting module {module}, sensor {sensor}, file {filename}, event {i_event} ...")

            # fig, ax = plt.subplots(figsize=(8, 8))
            # ax.scatter(group["hit_z"], group["hit_xp"], s=50)
            # ax.set_xlabel("z (mm)")
            # ax.set_ylabel("y (local) (mm)")
            # # ax.set_xlim([-825, -770])
            # # ax.set_ylim([816, 840])
            # ax.set_title(f"Hits on module {module}, sensor {sensor}")
            # ax.tick_params(direction="in", which="both", top=True, right=True)
            # fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            # pdf.savefig()
            # plt.close()

            # keep track of angles between layer 0 and layer 1
            df_0 = group[group["hit_layer"] == LAYERS[0]]
            df_1 = group[group["hit_layer"] == LAYERS[1]]
            if len(df_0) == 0 or len(df_1) == 0:
                continue

            # vectorized computation of angles
            x0 = df_0["hit_xp"].values[:, None]      # shape (N0, 1)
            x1 = df_1["hit_xp"].values[None, :]      # shape (1, N1)
            y0 = df_0["hit_yp"].values[:, None]      # shape (N0, 1)
            y1 = df_1["hit_yp"].values[None, :]      # shape (1, N1)
            z0 = df_0["hit_z"].values[:, None]       # shape (N0, 1)
            z1 = df_1["hit_z"].values[None, :]       # shape (1, N1)
            dx = x1 - x0                             # shape (N0, N1)
            dy = y1 - y0                             # shape (N0, N1)
            dz = z1 - z0                             # shape (N0, N1)
            xyangs = np.arctan2(dy, dx)              # shape (N0, N1)
            rzangs = np.arctan2(dz, dx)              # shape (N0, N1)
            zproj = z0 - x0 * np.tan(rzangs)         # shape (N0, N1)
            yproj = y0 - x0 * np.tan(xyangs)         # shape (N0, N1)
            if self.signal:
                if len(group["sim_pt"].unique()) != 1:
                    raise Exception("Expected unique sim_pt per group")
                pts = group["sim_pt"].unique()[0]
                pts = pts * np.ones_like(rzangs)
            else:
                pts = np.zeros_like(rzangs)

            # print("len(angles):", len(angles))
            # number of angles with angle > 1.4 and angle < 1.9
            lo, hi = -0.2, 0.2
            arr = np.array(rzangs)
            n_selected_rz = np.sum((arr > lo) & (arr < hi))

            lo, hi = -0.2, 0.2
            arr_xy = np.array(xyangs)
            n_selected_xy = np.sum((arr_xy > lo) & (arr_xy < hi))
            # print(f"module {module} sensor {sensor} layer {LAYERS[0]} hits: {len(df_0)}")
            # print(f"module {module} sensor {sensor} layer {LAYERS[1]} hits: {len(df_1)}")
            # print(f"module {module} sensor {sensor} total angles to compute: {len(rzangs)}")
            # print(f"module {module} sensor {sensor} number of r-z angles with angle > {lo} and angle < {hi}: {n_selected_rz}")
            # print(f"module {module} sensor {sensor} number of x-y angles with angle > {lo} and angle < {hi}: {n_selected_xy}")

            rzangles.extend(rzangs.ravel())
            xyangles.extend(xyangs.ravel())
            zprojs.extend(zproj.ravel())
            yprojs.extend(yproj.ravel())
            ptvalues.extend(pts.ravel())

            # debug
            if False and self.signal and np.max(np.abs(rzangs)) > 1.0 and n_debug < 100:
                n_debug += 1
                print("Debug: large rz angle found in signal event!")
                print(group)
                print()
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.scatter(group["hit_z"], group["hit_xp"], s=50)
                ax.set_xlabel("z (mm)")
                ax.set_ylabel("y (local) (mm)")
                ax.set_title(f"Hits on module {module}, sensor {sensor}")
                ax.text(0.05, 0.90, f"Event {i_event}, sim {i_sim}, {filename}", transform=ax.transAxes)
                dy = 4 if module % 2 == 1 else 0
                ax.set_xlim([-35, 5])
                ax.set_ylim([125 + dy, 131 + dy])
                ax.plot([-30, 0], [126.97 + dy, 126.97 + dy], color="gray", linestyle="-", alpha=0.3)
                ax.plot([-30, 0], [128.97 + dy, 128.97 + dy], color="gray", linestyle="-", alpha=0.3)
                ax.tick_params(direction="in", which="both", top=True, right=True)
                fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
                pdf.savefig()
                plt.close()

        # numpify
        rzangles = np.array(rzangles)
        xyangles = np.array(xyangles)
        ptvalues = np.array(ptvalues)
        zprojs = np.array(zprojs)
        yprojs = np.array(yprojs)
        lo, hi = -0.3, 0.3
        n_selected_rz = np.sum((rzangles > lo) & (rzangles < hi))
        n_selected_xy = np.sum((xyangles > lo) & (xyangles < hi))
        n_selected_rzxy = np.sum((rzangles > lo) & (rzangles < hi) & (xyangles > lo) & (xyangles < hi))
        print(f"Total number of r-z angles: {len(rzangles)}")
        print(f"Total number of x-y angles: {len(xyangles)}")
        print(f"Total number of r-z angles with angle > {lo} and angle < {hi}: {n_selected_rz}")
        print(f"Total number of x-y angles with angle > {lo} and angle < {hi}: {n_selected_xy}")
        print(f"Total number of angles with both r-z and x-y angle > {lo} and < {hi}: {n_selected_rzxy}")

        # plot r-z angle distribution
        print("Plotting r-z angle distribution ...")
        color = "blue" if self.signal else "red"
        fig, ax = plt.subplots(figsize=(8, 8))
        bins = np.linspace(-1.6, 1.6, 321)
        ax.hist(rzangles, bins=bins, color=color)
        ax.set_xlabel("r-z angle (rad)")
        ax.set_ylabel("Counts")
        ax.set_title(f"Angle between hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
        ax.tick_params(direction="in", which="both", top=True, right=True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
        pdf.savefig()
        # plt.close()

        ax.set_xlim([-1.60, -1.45])
        pdf.savefig()
        # plt.close()

        ax.set_xlim([1.45, 1.60])
        pdf.savefig()
        plt.close()

        # plot z projection in slices of pt
        if self.signal:
            print("Plotting z projection distribution in slices of pt ...")
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            bins = np.linspace(-1.0, 1.0, 201)
            for pt_lo, pt_hi in [
                (3, 4),
                (2, 3),
                (1, 2),
                (0, 1),
            ]:
                mask = (ptvalues >= pt_lo) & (ptvalues < pt_hi)
                rzangles_pt = rzangles[mask]
                ax.hist(rzangles_pt, bins=bins, linewidth=2, histtype="step", label=f"pt {pt_lo}-{pt_hi} GeV")
            # ax.hist(xyangles, bins=bins, color=color)
            ax.set_xlabel("z projection (mm)")
            ax.set_ylabel("Counts")
            ax.set_title(f"z-proj. for hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            ax.legend()
            ax.grid()
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # plot x-y angle distribution
        print("Plotting x-y angle distribution ...")
        color = "blue" if self.signal else "red"
        fig, ax = plt.subplots(figsize=(8, 8))
        bins = np.linspace(-1.6, 1.6, 321)
        ax.hist(xyangles, bins=bins, color=color)
        ax.set_xlabel("x-y angle (rad)")
        ax.set_ylabel("Counts")
        ax.set_title(f"Angle between hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
        ax.tick_params(direction="in", which="both", top=True, right=True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
        pdf.savefig()
        # plt.close()

        ax.set_xlim([-1.60, -1.45])
        pdf.savefig()
        # plt.close()

        ax.set_xlim([1.45, 1.60])
        pdf.savefig()
        plt.close()

        # plot x-y angle distribution in slices of pt
        if self.signal:
            print("Plotting x-y angle distribution in slices of pt ...")
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            bins = np.linspace(-1.6, 1.6, 161)
            for pt_lo, pt_hi in [
                # (7, 10),
                # (4, 7),
                # (2, 4),

                (3, 4),
                (2, 3),

                # (10, 11),
                # (9, 10),
                # (8, 9),
                # (7, 8),
                # (6, 7),
                # (5, 6),
                # (4, 5),
                # (3, 4,),
                # (2, 3),
                (1, 2),
                (0, 1),
            ]:
                mask = (ptvalues >= pt_lo) & (ptvalues < pt_hi)
                xyangles_pt = xyangles[mask]
                ax.hist(xyangles_pt, bins=bins, linewidth=2, histtype="step", label=f"pt {pt_lo}-{pt_hi} GeV")
            # ax.hist(xyangles, bins=bins, color=color)
            ax.set_xlabel("x-y angle (rad)")
            ax.set_ylabel("Counts")
            ax.set_title(f"Angle between hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            ax.legend()
            ax.grid()
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # z-projection
        print("Plotting z-projection distribution ...")
        for bins in [
            100,
            np.linspace(-2200, 2200, 441),
            np.linspace(-60, 60, 121),
        ]:
            # plot zproj distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.hist(zprojs, bins=bins, color=color)
            ax.set_xlabel("z projection (mm)")
            ax.set_ylabel("Counts")
            ax.set_title(f"z-proj. for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # plot z projection in slices of pt
        if self.signal:
            print("Plotting z projection distribution in slices of pt ...")
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            bins = np.linspace(-50, 50, 201)
            for pt_lo, pt_hi in [
                (3, 4),
                (2, 3),
                (1, 2),
                (0, 1),
            ]:
                mask = (ptvalues >= pt_lo) & (ptvalues < pt_hi)
                zprojs_pt = zprojs[mask]
                ax.hist(zprojs_pt, bins=bins, linewidth=2, histtype="step", label=f"pt {pt_lo}-{pt_hi} GeV")
            # ax.hist(xyangles, bins=bins, color=color)
            ax.set_xlabel("z projection (mm)")
            ax.set_ylabel("Counts")
            ax.set_title(f"z-proj. for hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            ax.legend()
            ax.grid()
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # y-projection
        print("Plotting y-projection distribution ...")
        for bins in [
            100,
            np.linspace(-2200, 2200, 441),
            np.linspace(-200, 200, 201),
            np.linspace(-60, 60, 121),
        ]:
            # plot yproj distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.hist(yprojs, bins=bins, color=color)
            ax.set_xlabel("y projection (mm)")
            ax.set_ylabel("Counts")
            ax.set_title(f"y-proj. for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()

        # plot y projection in slices of pt
        if self.signal:
            print("Plotting y projection distribution in slices of pt ...")
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            bins = np.linspace(-50, 50, 201)
            for pt_lo, pt_hi in [
                (3, 4),
                (2, 3),
                (1, 2),
                (0, 1),
            ]:
                mask = (ptvalues >= pt_lo) & (ptvalues < pt_hi)
                yprojs_pt = yprojs[mask]
                ax.hist(yprojs_pt, bins=bins, linewidth=2, histtype="step", label=f"pt {pt_lo}-{pt_hi} GeV")
            # ax.hist(xyangles, bins=bins, color=color)
            ax.set_xlabel("y projection (mm)")
            ax.set_ylabel("Counts")
            ax.set_title(f"y-proj. for hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            ax.legend()
            ax.grid()
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # rz vs xy hist2d
        print("Plotting z-projection distribution ...")
        for bins in [
            100,
        ]:
            # plot zproj distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            _, _, _, im = ax.hist2d(rzangles, xyangles, bins=bins, cmap="gist_rainbow", cmin=0.5)
            ax.set_xlabel("r-z angle (rad)")
            ax.set_ylabel("x-y angle (rad)")
            ax.set_title(f"rz vs xy angles for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            fig.colorbar(im, ax=ax, pad=0.01, label="Hit pairs")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # rz vs zproj hist2d
        print("Plotting z-projection distribution ...")
        for bins in [
            100,
             [np.linspace(-1.6, 1.6, 161),
              np.linspace(-60, 60, 121)],
             [np.linspace(-0.5, 0.5, 101),
              np.linspace(-25, 25, 101)],
        ]:
            # plot zproj distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            _, _, _, im = ax.hist2d(rzangles, zprojs, bins=bins, cmap="gist_rainbow", cmin=0.5)
            ax.set_xlabel("r-z angle (rad)")
            ax.set_ylabel("z projection (mm)")
            ax.set_title(f"rz vs z projection for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            fig.colorbar(im, ax=ax, pad=0.01, label="Hit pairs")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # yproj vs zproj hist2d
        print("Plotting y-projection vs z-projection distribution ...")
        for bins in [
            100,
             [np.linspace(-2100, 2100, 106),
              np.linspace(-2100, 2100, 106)],
             [np.linspace(-60, 60, 121),
              np.linspace(-60, 60, 121)],
             [np.linspace(-30, 30, 121),
              np.linspace(-30, 30, 121)],
        ]:
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            _, _, _, im = ax.hist2d(yprojs, zprojs, bins=bins, cmap="gist_rainbow", cmin=0.5)
            ax.set_xlabel("y projection (mm)")
            ax.set_ylabel("z projection (mm)")
            ax.set_title(f"y vs z projection for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            fig.colorbar(im, ax=ax, pad=0.01, label="Hit pairs")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()



if __name__ == "__main__":
    main()
