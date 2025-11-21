import argparse
from glob import glob

INNER_BARREL = "IBTrackerHits" # "InnerTrackerBarrelCollection"
OUTER_BARREL = "OBTrackerHits" # "OuterTrackerBarrelCollection"
from slcio_to_hits_dataframe import SlcioToHitsDataFrame

SIDE = 0
LAYERS = [0, 1]
SENSORS = [15]
MODULES = range(30)


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", type=str,
                        help="Comma-separated list of globbable input slcio files for signal")
    parser.add_argument("-b", type=str,
                        help="Comma-separated list of globbable input slcio files for background")
    return parser.parse_args()


def main():
    ops = options()

    # command line inputs
    if not ops.s:
        raise Exception("Please give input signal file(s) with -s")
    if not ops.b:
        raise Exception("Please give input background file(s) with -b")
    sig_paths = get_files(ops.s)
    bkg_paths = get_files(ops.b)
    for path in sig_paths:
        print(f"Input signal file: {path}")
    for path in bkg_paths:
        print(f"Input background file: {path}")

    # load the data
    sig_df = SlcioToHitsDataFrame(sig_paths, [INNER_BARREL], LAYERS, SENSORS).convert()
    bkg_df = SlcioToHitsDataFrame(bkg_paths, [INNER_BARREL], LAYERS, SENSORS).convert()
    print(sig_df)
    print(bkg_df)

    # for df, name in [(sig_df, "signal"),
    #                  (bkg_df, "background")]:
    #     print(f"{name} hits: {len(df)}")
    #     print(f"{name} unique events: {df['file'].nunique()},{df['i_event'].nunique()}")

    # make plots
    for df, pdf in [
        # (sig_df, "sig_plots.pdf"),
        (bkg_df, "bkg_plots.pdf"),
    ]:
        print(f"Making plots for {pdf} ...")
        plotter = Plotter(df, pdf)
        plotter.plot()


def get_files(pattern: str, max_files: int = 0) -> list[str]:
    files = []
    for fi in pattern.split(","):
        files.extend(glob(fi))
    files.sort()
    if max_files > 0:
        files = files[:max_files]
    return files

##########################################################################################

# Put this in a different file soon
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({'font.size': 16})

from constants import BARREL_RADII

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
        angles = []
        xyangles = []
        for ((sensor, module, filename, i_event), group) in self.df.groupby(['hit_sensor', 'hit_module', 'file', 'i_event']):
        # for sensor in SENSORS:
            # for module in MODULES:
                # if module > 2:
                #     break
            # mask = (group['hit_module'] == module) & (group['hit_sensor'] == sensor)
            # df =  group[mask]
            if len(group) == 0:
                continue
            print(f"Plotting module {module}, sensor {sensor}, file {filename}, event {i_event} ...")

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

            angs = []
            xyangs = []
            for _, hit_0 in df_0.iterrows():
                for _, hit_1 in df_1.iterrows():
                    dx = hit_1['hit_xp'] - hit_0['hit_xp']
                    dz = hit_1['hit_z'] - hit_0['hit_z']
                    dy = hit_1['hit_yp'] - hit_0['hit_yp']
                    xyangs.append(np.arctan2(dy, dx))
                    angs.append(np.arctan2(dx, dz))
            # print("len(angles):", len(angles))
            # number of angles with angle > 1.4 and angle < 1.9
            lo, hi = 1.4, 1.9
            arr = np.array(angs)
            n_selected = np.sum((arr > lo) & (arr < hi))

            lo, hi = -0.2, 0.2
            arr_xy = np.array(xyangs)
            n_selected_xy = np.sum((arr_xy > lo) & (arr_xy < hi))
            print(f"module {module} sensor {sensor} layer {LAYERS[0]} hits: {len(df_0)}")
            print(f"module {module} sensor {sensor} layer {LAYERS[1]} hits: {len(df_1)}")
            print(f"module {module} sensor {sensor} total angles to compute: {len(angs)}")
            print(f"module {module} sensor {sensor} number of angles with angle > {lo} and angle < {hi}: {n_selected}")
            print(f"module {module} sensor {sensor} number of x-y angles with angle > {lo} and angle < {hi}: {n_selected_xy}")

            angles.extend(angs)
            xyangles.extend(xyangs)

            #         break
            #     break
            # break


        # plot r-z angle distribution
        color = "blue" if self.signal else "red"
        fig, ax = plt.subplots(figsize=(8, 8))
        bins = np.linspace(-0.1, 3.2, 331)
        ax.hist(angles, bins=bins, color=color)
        ax.set_xlabel("r-z angle (rad)")
        ax.set_ylabel("Counts")
        ax.set_title(f"Angle between hits in layer {LAYERS[0]} and {LAYERS[1]}, sensor {sensor}")
        ax.set_xlim([0.0, np.pi])
        ax.tick_params(direction="in", which="both", top=True, right=True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
        pdf.savefig()
        # plt.close()

        ax.set_xlim([-0.04, 0.12])
        pdf.savefig()
        # plt.close()

        ax.set_xlim([3.0, 3.16])
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
        plt.close()

        # ax.set_xlim([-0.04, 0.12])
        # pdf.savefig()
        # plt.close()

        # ax.set_xlim([3.0, 3.16])
        # pdf.savefig()
        # plt.close()


if __name__ == "__main__":
    main()
