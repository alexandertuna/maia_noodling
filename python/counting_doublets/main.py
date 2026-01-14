import argparse
from glob import glob
import pandas as pd

from slcio import SlcioToHitsDataFrame
from timelapse import Timelapse
from doublet import DoubletMaker
from plot import Plotter

FNAMES = [
    # neutrinoGun 100%
    # "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2026_01_08_13h45m00s/prod_00/neutrinoGun_digi_1.slcio",

    # neutrinoGun 10%
    # "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2026_01_11_21h02m00s/prod_00/neutrinoGun_digi_1.slcio",

    # muonGun
    "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_12_20_17h26m00s/muonGun_pT_0_10_sim_10*.slcio",
]


def main():
    ops = options()
    fnames = get_filenames(ops.i)
    geometry = ops.geometry

    converter = SlcioToHitsDataFrame(slcio_file_paths=fnames,
                                     load_geometry=geometry)
    mcps, simhits = converter.convert()
    print(mcps)
    print(simhits)

    doublets = DoubletMaker(simhits=simhits).df
    # print(doublets)

    plotter = Plotter(
        mcps=mcps,
        doublets=doublets,
        pdf="doublets.pdf",
    )
    plotter.plot()



    # print("Creating timelapse gif ...")
    # tl = Timelapse(df=df, event=0, gif="event.gif")


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", default=FNAMES, help="Input slcio file or glob pattern")
    parser.add_argument("--geometry", action="store_true", help="Load compact geometry from xml")
    return parser.parse_args()


def get_filenames(fnames):
    names = []
    if isinstance(fnames, str):
        fnames = [fnames]
    for fname in fnames:
        names.extend(glob(fname))
    return names


if __name__ == "__main__":
    main()
