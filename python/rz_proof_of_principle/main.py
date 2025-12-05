import argparse
from glob import glob
import pandas as pd

INNER_BARREL_SIM = "InnerTrackerBarrelCollection"
INNER_BARREL_REL = "IBTrackerHitsRelations" # digi

from slcio_to_hits_dataframe import SlcioToHitsDataFrame
from plot import Plotter
from constants import SIDE, LAYERS, SENSORS, MODULES


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", type=str,
                        help="Comma-separated list of globbable input slcio files for signal")
    parser.add_argument("-b", type=str,
                        help="Comma-separated list of globbable input slcio files for background")
    parser.add_argument("--signal_parquet", type=str, default="sig.parquet",
                        help="Output parquet file for signal hits dataframe")
    parser.add_argument("--background_parquet", type=str, default="bkg.parquet",
                        help="Output parquet file for background hits dataframe")
    parser.add_argument("--load_parquet", action="store_true",
                        help="Load from parquet files instead of slcio files")
    return parser.parse_args()


def main():
    ops = options()
    if ops.load_parquet and (ops.s or ops.b):
        raise Exception("Either load from parquet (--load_parquet) or from slcio files (-s and -b), not both.")

    if not ops.load_parquet:
        # get slcio file names
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

        # convert slcio to hits dataframe
        sig_df = SlcioToHitsDataFrame(sig_paths, [INNER_BARREL_SIM], LAYERS, SENSORS, signal=True).convert()
        bkg_df = SlcioToHitsDataFrame(bkg_paths, [INNER_BARREL_REL], LAYERS, SENSORS, signal=False).convert()

        # write to parquet
        sig_df.to_parquet(ops.signal_parquet)
        bkg_df.to_parquet(ops.background_parquet)

    else:
        print("Loading from parquet files ...")
        sig_df = pd.read_parquet(ops.signal_parquet)
        bkg_df = pd.read_parquet(ops.background_parquet)

    print(sig_df)
    print(bkg_df)

    # make plots
    for df, pdf in [
        (sig_df, "sig_plots.pdf"),
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


if __name__ == "__main__":
    main()
