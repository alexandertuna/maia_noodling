import argparse
from glob import glob
import os
import pandas as pd

from slcio import SlcioToHitsDataFrame
from timelapse import Timelapse
from doublet import DoubletMaker
from plot import Plotter

FNAMES = [
    # neutrinoGun 100%
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun/neutrinoGun_digi_1.slcio",

    # neutrinoGun 10%
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_0.10/neutrinoGun_digi_1.slcio",

    # muonGun
    "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_12_20_17h26m00s/muonGun_pT_0_10_sim_1*.slcio",
]


def main():
    ops = options()
    fnames = get_filenames(ops.i)
    geometry = ops.geometry
    signal = any("muonGun" in os.path.basename(fname) for fname in fnames)
    print(f"Detected {'signal' if signal else 'background'} files")

    converter = SlcioToHitsDataFrame(slcio_file_paths=fnames,
                                     load_geometry=geometry)
    mcps, simhits = converter.convert()
    print("MC Particles:")
    print(mcps)
    print("Sim hits:")
    print(simhits)

    doublets = DoubletMaker(simhits=simhits).df
    if not signal:
        # drop simhit_r_upper, ... for a speedup
        print("Dropping simhit_{x,y,z}_{upper,lower} columns from doublets ...")
        doublets = doublets.drop(columns=[
            "simhit_r_upper",
            "simhit_r_lower",
            "simhit_x_upper",
            "simhit_x_lower",
            "simhit_y_upper",
            "simhit_y_lower",
            "simhit_z_upper",
            "simhit_z_lower",
        ])
    print("Doublets:")
    print(doublets)

    plotter = Plotter(
        signal=signal,
        mcps=mcps,
        simhits=simhits,
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
