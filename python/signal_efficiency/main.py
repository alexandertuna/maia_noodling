import argparse
from glob import glob
import pandas as pd
import time

from slcio_to_hits import SlcioToHitsDataFrame
from event_displays import EventDisplays
from plot import Plotter

FNAMES = [
    # v01
    "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_12_20_17h26m00s/muonGun_pT_0_10_sim_1*.slcio",

    # v00
    # "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_1*.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_2*.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_3*.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_4*.slcio",
]
NOW = time.strftime("%Y_%m_%d_%Hh%Mm%Ss")
PDF = f"detector_efficiency_NOW.pdf"
DISPLAYS = "event_displays_NOW.pdf"
PARQUET = f"detector_efficiency_NOW.parquet"
PRINT_GROUPS = 0


def main():
    ops = options()
    fnames = get_filenames(FNAMES)
    geometry = ops.geometry
    df = SlcioToHitsDataFrame(slcio_file_paths=fnames, load_geometry=geometry).convert()

    # write df to file
    if ops.write_to_parquet:
        print(f"Writing data frame to {PARQUET}...")
        df.to_parquet(PARQUET)

    # show some info
    group_cols = ["file", "i_event", "i_mcp"]
    for i_group, (cols, group) in enumerate(df.groupby(group_cols)):
        if i_group >= PRINT_GROUPS:
            break
        mask = group["simhit"]
        cols = ["i_event",
                "i_mcp",
                "mcp_pt",
                "mcp_eta",
                "mcp_phi",
                "mcp_pdg",
                "simhit_system",
                "simhit_layer",
                "simhit_module",
                "simhit_sensor",
                "simhit_eta",
                "simhit_phi",
                "simhit_t",
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

    # make event displays
    if ops.event_displays:
        print(f"Making event displays to {DISPLAYS}...")
        displays = EventDisplays(df, DISPLAYS)
        displays.make_event_displays()

    # show the dataframe
    # with pd.option_context("display.min_rows", 50,
    #                        "display.max_rows", 50,
    #                       ):
    #     print(df)

    plotter = Plotter(df, PDF, geometry)
    plotter.plot()


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--geometry", action="store_true", help="Load compact geometry from xml")
    parser.add_argument("--event-displays", action="store_true", help="Make event displays")
    parser.add_argument("--write-to-parquet", action="store_true", help="Write dataframe to parquet file")
    return parser.parse_args()


def get_filenames(fnames):
    names = []
    for fname in fnames:
        names.extend(glob(fname))
    return names


if __name__ == "__main__":
    main()
