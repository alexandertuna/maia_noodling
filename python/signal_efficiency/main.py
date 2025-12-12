import pandas as pd
from slcio_to_hits import SlcioToHitsDataFrame
from plot import Plotter

FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_100.slcio"
COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
PDF = "signal_efficiency.pdf"

def main():
    df = SlcioToHitsDataFrame(
        slcio_file_paths=[FNAME],
        collections=COLLECTIONS,
    ).convert()

    # show the dataframe
    with pd.option_context("display.min_rows", 50,
                           "display.max_rows", 50,
                          ):
        print(df)

    plotter = Plotter(df, PDF)
    plotter.plot()

if __name__ == "__main__":
    main()
