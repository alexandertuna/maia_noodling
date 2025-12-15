from glob import glob
import pandas as pd
import time

from slcio_to_hits import SlcioToHitsDataFrame
from plot import Plotter

FNAMES = [
    "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_1*.slcio",
]
COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
NOW = time.strftime("%Y_%m_%d_%Hh%Mm%Ss")
PDF = f"detector_efficiency_NOW.pdf"
PARQUET = f"detector_efficiency_NOW.parquet"
PRINT_GROUPS = 0


def main():
    fnames = get_filenames(FNAMES)
    df = SlcioToHitsDataFrame(
        slcio_file_paths=fnames,
        collections=COLLECTIONS,
    ).convert()

    # write df to file
    print(f"Writing data frame to {PARQUET}...")
    df.to_parquet(PARQUET)

    # show some info
    group_cols = ["file", "i_event", "i_mcp"]
    for i_group, (cols, group) in enumerate(df.groupby(group_cols)):
        if i_group >= PRINT_GROUPS:
            break
        mask = group["hit"]
        cols = ["i_event",
                "i_mcp",
                "mcp_pt",
                "mcp_eta",
                "mcp_phi",
                "mcp_pdg",
                "hit_system",
                "hit_layer",
                "hit_module",
                "hit_sensor",
                "hit_eta",
                "hit_phi",
                "hit_t",
                ]
        linebreak = "-"*30
        print(f"{linebreak} mcparticle {i_group} {linebreak}")
        with pd.option_context("display.min_rows", 50,
                               "display.max_rows", 50,
                               "display.max_columns", None,
                               "display.width", None,
                               "display.max_colwidth", None,
                            ):
            print(group[mask][cols].to_string(index=False))


    # show the dataframe
    # with pd.option_context("display.min_rows", 50,
    #                        "display.max_rows", 50,
    #                       ):
    #     print(df)

    plotter = Plotter(df, PDF)
    plotter.plot()


def get_filenames(fnames):
    names = []
    for fname in fnames:
        names.extend(glob(fname))
    return names


if __name__ == "__main__":
    main()
