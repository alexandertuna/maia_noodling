import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({'font.size': 16})

from constants import BARREL_RADII
from constants import SIDE, LAYERS, SENSORS, MODULES

class Plotter:

    def __init__(self, df: pd.DataFrame, pdf_path: str):
        self.df = df
        self.pdf_path = pdf_path
        self.signal = "sig" in pdf_path.lower()

        self.df["module_angle"] = -1 * self.df["hit_module"] * (2.0 * np.pi / len(MODULES))
        self.df["hit_xp"] = self.df["hit_x"] * np.cos(self.df["module_angle"]) - self.df["hit_y"] * np.sin(self.df["module_angle"])
        self.df["hit_yp"] = self.df["hit_x"] * np.sin(self.df["module_angle"]) + self.df["hit_y"] * np.cos(self.df["module_angle"])


    def plot(self):
        with PdfPages(self.pdf_path) as pdf:
            self.plot_xy(pdf)
            self.plot_rz(pdf)
            self.plot_rz_events(pdf)


    def plot_xy(self, pdf: PdfPages):
        for module in MODULES:
            mask = self.df['hit_module'] == module
            df_module = self.df[mask]
            if len(df_module) == 0:
                continue
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.scatter(df_module['hit_x'], df_module['hit_y'], s=10)
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("y (mm)")
            ax.set_title(f"x vs y of Hits - Module {module}")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.1)
            pdf.savefig()
            plt.close()


    def plot_rz(self, pdf: PdfPages):
        for sensor in SENSORS:
            for module in MODULES:
                print(f"Plotting module {module} ...")
                mask = (self.df['hit_module'] == module) & (self.df['hit_sensor'] == sensor)
                df_module = self.df[mask]
                if len(df_module) == 0:
                    continue
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.scatter(df_module['hit_z'], df_module['hit_xp'], s=50)
                ax.set_xlabel("z (mm)")
                ax.set_ylabel("y (local) (mm)")
                # ax.set_xlim([-825, -770])
                # ax.set_ylim([816, 840])
                ax.set_title(f"Hits on module {module}, sensor {sensor}")
                ax.tick_params(direction='in', which='both', top=True, right=True)
                fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
                pdf.savefig()
                plt.close()


    def plot_rz_events(self, pdf: PdfPages):

        rzangles = []
        xyangles = []
        n_debug = 0

        for ((sensor, module, filename, i_event, i_sim), group) in self.df.groupby(['hit_sensor',
                                                                                    'hit_module',
                                                                                    'file',
                                                                                    'i_event',
                                                                                    'i_sim',
                                                                                    ]):

            if len(group) == 0:
                continue
            # print(f"Plotting module {module}, sensor {sensor}, file {filename}, event {i_event} ...")

            # fig, ax = plt.subplots(figsize=(8, 8))
            # ax.scatter(group['hit_z'], group['hit_xp'], s=50)
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
            df_0 = group[group['hit_layer'] == LAYERS[0]]
            df_1 = group[group['hit_layer'] == LAYERS[1]]
            if len(df_0) == 0 or len(df_1) == 0:
                continue

            # vectorized computation of angles
            x0 = df_0['hit_xp'].values[:, None]      # shape (N0, 1)
            x1 = df_1['hit_xp'].values[None, :]      # shape (1, N1)
            y0 = df_0['hit_yp'].values[:, None]      # shape (N0, 1)
            y1 = df_1['hit_yp'].values[None, :]      # shape (1, N1)
            z0 = df_0['hit_z'].values[:, None]       # shape (N0, 1)
            z1 = df_1['hit_z'].values[None, :]       # shape (1, N1)
            dx = x1 - x0                             # shape (N0, N1)
            dy = y1 - y0                             # shape (N0, N1)
            dz = z1 - z0                             # shape (N0, N1)
            xyangs = np.arctan2(dy, dx).ravel()       # flatten to 1D if needed
            rzangs = np.arctan2(dz, dx).ravel()       # flatten to 1D if needed

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

            rzangles.extend(rzangs)
            xyangles.extend(xyangs)

            # debug
            if False and self.signal and np.max(np.abs(rzangs)) > 1.0 and n_debug < 100:
                n_debug += 1
                print("Debug: large rz angle found in signal event!")
                print(group)
                print()
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.scatter(group['hit_z'], group['hit_xp'], s=50)
                ax.set_xlabel("z (mm)")
                ax.set_ylabel("y (local) (mm)")
                ax.set_title(f"Hits on module {module}, sensor {sensor}")
                ax.text(0.05, 0.90, f"Event {i_event}, sim {i_sim}, {filename}", transform=ax.transAxes)
                dy = 4 if module % 2 == 1 else 0
                ax.set_xlim([-35, 5])
                ax.set_ylim([125 + dy, 131 + dy])
                ax.plot([-30, 0], [126.97 + dy, 126.97 + dy], color='gray', linestyle='-', alpha=0.3)
                ax.plot([-30, 0], [128.97 + dy, 128.97 + dy], color='gray', linestyle='-', alpha=0.3)
                ax.tick_params(direction="in", which="both", top=True, right=True)
                fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
                pdf.savefig()
                plt.close()

        # numpify
        rzangles = np.array(rzangles)
        xyangles = np.array(xyangles)
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

        # plot x-y angle distribution
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


if __name__ == "__main__":
    main()
