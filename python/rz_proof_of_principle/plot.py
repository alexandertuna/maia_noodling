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
            self.plot_hit_time(pdf)
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


    def plot_hit_time(self, pdf: PdfPages):
        bins = np.linspace(-12, 24, 181)

        fig, ax = plt.subplots(figsize=(8, 8))
        color = "blue" if self.signal else "red"
        ax.hist(self.df["hit_t"], bins=bins, color=color)
        ax.set_xlabel("Hit time [ns]")
        ax.set_ylabel("Counts")
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.grid()
        ax.set_axisbelow(True)
        ax.semilogy()
        ax.set_ylim([0.5, None])
        fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots(figsize=(8, 8))
        color = "blue" if self.signal else "red"
        ax.hist(self.df["hit_t_corrected"], bins=bins, color=color)
        ax.set_xlabel("Hit time, corrected for time-of-flight [ns]")
        ax.set_ylabel("Counts")
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.grid()
        ax.set_axisbelow(True)
        ax.semilogy()
        ax.set_ylim([0.5, None])
        fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
        pdf.savefig()
        plt.close()




    def plot_rz_events(self, pdf: PdfPages):

        rzangles = []
        xpzangles = []
        xyangles = []
        ptvalues = []
        rzprojs = []
        xpzprojs = []
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
            r0 = df_0["hit_r"].values[:, None]       # shape (N0, 1)
            r1 = df_1["hit_r"].values[None, :]       # shape (1, N1)
            dx = x1 - x0                             # shape (N0, N1)
            dy = y1 - y0                             # shape (N0, N1)
            dz = z1 - z0                             # shape (N0, N1)
            dr = r1 - r0                             # shape (N0, N1)
            xyangs = np.arctan2(dy, dx)              # shape (N0, N1)
            rzangs = np.arctan2(dz, dr)              # shape (N0, N1)
            xpzangs = np.arctan2(dz, dx)             # shape (N0, N1)
            xpzproj = z0 - x0 * np.tan(xpzangs)      # shape (N0, N1)
            rzproj = z0 - r0 * np.tan(rzangs)        # shape (N0, N1)
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

            xpzangles.extend(xpzangs.ravel())
            rzangles.extend(rzangs.ravel())
            xyangles.extend(xyangs.ravel())
            xpzprojs.extend(xpzproj.ravel())
            rzprojs.extend(rzproj.ravel())
            yprojs.extend(yproj.ravel())
            ptvalues.extend(pts.ravel())


        # numpify
        xpzangles = np.array(xpzangles)
        rzangles = np.array(rzangles)
        xyangles = np.array(xyangles)
        ptvalues = np.array(ptvalues)
        xpzprojs = np.array(xpzprojs)
        rzprojs = np.array(rzprojs)
        yprojs = np.array(yprojs)
        lo, hi = -0.3, 0.3
        n_selected_xpz = np.sum((xpzangles > lo) & (xpzangles < hi))
        n_selected_xy = np.sum((xyangles > lo) & (xyangles < hi))
        n_selected_xpzxy = np.sum((xpzangles > lo) & (xpzangles < hi) & (xyangles > lo) & (xyangles < hi))
        print(f"Total number of xp-z angles: {len(xpzangles)}")
        print(f"Total number of x-y angles: {len(xyangles)}")
        print(f"Total number of xp-z angles with angle > {lo} and angle < {hi}: {n_selected_xpz}")
        print(f"Total number of x-y angles with angle > {lo} and angle < {hi}: {n_selected_xy}")
        print(f"Total number of angles with both xp-z and x-y angle > {lo} and < {hi}: {n_selected_xpzxy}")


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


        # plot xp-z angle distribution
        print("Plotting xp-z angle distribution ...")
        color = "blue" if self.signal else "red"
        fig, ax = plt.subplots(figsize=(8, 8))
        bins = np.linspace(-1.6, 1.6, 321)
        ax.hist(xpzangles, bins=bins, color=color)
        ax.set_xlabel("xp-z angle (rad)")
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

        # plot xp-z angles in slices of pt
        if self.signal:
            print("Plotting xp-z angle distribution in slices of pt ...")
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
                xpzangles_pt = xpzangles[mask]
                ax.hist(xpzangles_pt, bins=bins, linewidth=2, histtype="step", label=f"pt {pt_lo}-{pt_hi} GeV")
            # ax.hist(xyangles, bins=bins, color=color)
            ax.set_xlabel("xp-z angle (rad)")
            ax.set_ylabel("Counts")
            ax.set_title(f"Angle between hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            ax.legend()
            ax.grid()
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # plot r-z angles in slices of pt
        if self.signal:
            print("Plotting r-z angle distribution in slices of pt ...")
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
            ax.set_xlabel("r-z angle (rad)")
            ax.set_ylabel("Counts")
            ax.set_title(f"Angle between hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
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
                (3, 4),
                (2, 3),
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
            np.linspace(-2, 2, 121),
        ]:
            # plot xpzproj distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.hist(xpzprojs, bins=bins, color=color)
            ax.set_xlabel("(x') z projection (mm)")
            ax.set_ylabel("Counts")
            ax.set_title(f"(x') z-proj. for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()


        # z-projection
        print("Plotting rz-projection distribution ...")
        for bins in [
            100,
            np.linspace(-2200, 2200, 441),
            np.linspace(-60, 60, 121),
            np.linspace(-2, 2, 121),
        ]:
            # plot zproj distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.hist(rzprojs, bins=bins, color=color)
            ax.set_xlabel("(r) z-projection (mm)")
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
                xpzprojs_pt = xpzprojs[mask]
                ax.hist(xpzprojs_pt, bins=bins, linewidth=2, histtype="step", label=f"pt {pt_lo}-{pt_hi} GeV")
            ax.set_xlabel("(x') z projection (mm)")
            ax.set_ylabel("Counts")
            ax.set_title(f"(x') z-proj. for hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
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
            for bins in [
                np.linspace(-500, 500, 201),
                np.linspace(-50, 50, 201),
            ]:
                print("Plotting y projection distribution in slices of pt ...")
                color = "blue" if self.signal else "red"
                fig, ax = plt.subplots(figsize=(8, 8))
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


        # xp-z vs xy hist2d
        print("Plotting xp-z vs xy distribution ...")
        for bins in [
            100,
        ]:
            # plot xp-z vs xy distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            _, _, _, im = ax.hist2d(xpzangles, xyangles, bins=bins, cmap="gist_rainbow", cmin=0.5)
            ax.set_xlabel("xp-z angle (rad)")
            ax.set_ylabel("x-y angle (rad)")
            ax.set_title(f"xp-z vs xy angles for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
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
              np.linspace(-2, 2, 101)],
        ]:
            # plot zproj distribution
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            _, _, _, im = ax.hist2d(xpzangles, xpzprojs, bins=bins, cmap="gist_rainbow", cmin=0.5)
            ax.set_xlabel("xp-z angle (rad)")
            ax.set_ylabel("(xp) z projection (mm)")
            ax.set_title(f"xp-z vs (xp) z projection for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
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
             [np.linspace(-10, 10, 121),
              np.linspace(-10, 10, 121)],
        ]:
            color = "blue" if self.signal else "red"
            fig, ax = plt.subplots(figsize=(8, 8))
            _, _, _, im = ax.hist2d(yprojs, xpzprojs, bins=bins, cmap="gist_rainbow", cmin=0.5)
            ax.set_xlabel("y projection (mm)")
            ax.set_ylabel("(xp) z projection (mm)")
            ax.set_title(f"y vs (xp) z projection for hits in layers {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
            ax.tick_params(direction="in", which="both", top=True, right=True)
            fig.colorbar(im, ax=ax, pad=0.01, label="Hit pairs")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
            pdf.savefig()
            plt.close()



if __name__ == "__main__":
    main()
