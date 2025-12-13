from glob import glob
import pandas as pd
from slcio_to_hits import SlcioToHitsDataFrame
from plot import Plotter

FNAMES = [
    "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_1*.slcio",
]
COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
PDF = "signal_efficiency.pdf"
PRINT_GROUPS = 0


def main():
    fnames = get_filenames(FNAMES)
    df = SlcioToHitsDataFrame(
        slcio_file_paths=fnames,
        collections=COLLECTIONS,
    ).convert()

    # show some info
    group_cols = ["file", "i_event", "i_sim"]
    for i_group, (cols, group) in enumerate(df.groupby(group_cols)):
        if i_group >= PRINT_GROUPS:
            break
        mask = group["hit"]
        cols = ["i_event",
                "i_sim",
                "sim_pt",
                "sim_eta",
                "sim_phi",
                "sim_pdg",
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
