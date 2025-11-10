import argparse
import pandas as pd
from glob import glob

from slcio_to_hits_dataframe import SlcioToHitsDataFrame
from hits_sorted_by_module import GetNextHitAndSort
from hits_to_module_map import HitsToModuleMap
from plotter import Plotter

# FNAME = "/ceph/users/atuna/work/maia/maia_noodling/samples/v00/muonGun_pT_0_10_nobib/muonGun_pT_0_10_digi_0.slcio"
FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_digi_0.slcio"

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default=FNAME,
                        help="Comma-separated list of globbable input slcio files")
    parser.add_argument("--parquet", type=str, default="hits_dataframe.parquet",
                        help="Intermediate parquet file for hits dataframe")
    parser.add_argument("--load_parquet", action="store_true",
                        help="Load hits dataframe from parquet file")
    parser.add_argument("--barrel_only", action="store_true",
                        help="Consider only barrel hits for module mapping")
    return parser.parse_args()


def main():
    ops = options()
    file_paths = get_files(ops.i)
    for fpath in file_paths:
        print(f"Input file: {fpath}")

    if ops.load_parquet:
        hits_df = pd.read_parquet(ops.parquet)
    else:
        converter = SlcioToHitsDataFrame(file_paths, barrel_only=ops.barrel_only)
        hits_df = converter.convert()
        print(f"Writing hits to {ops.parquet} ...")
        hits_df.to_parquet(ops.parquet)
    print(hits_df)
    # with pd.option_context("display.min_rows", 100,
    #                        "display.max_rows", 100,
    #                        ):
    #     print(hits_df)

    next_hitter = GetNextHitAndSort(hits_df)
    sorted_df = next_hitter.get_next_hit_and_sort_by_module()
    sorted_df.to_parquet("sorted_hits.parquet")

    module_mapper = HitsToModuleMap(sorted_df)
    module_map_df = module_mapper.make_module_map()
    print(module_map_df)

    plotter = Plotter(hits_df, sorted_df, module_map_df)
    plotter.plot("plots.pdf")

def get_files(pattern: str) -> list[str]:
    files = []
    for fi in pattern.split(","):
        files.extend(glob(fi))
    return files


if __name__ == "__main__":
    main()
