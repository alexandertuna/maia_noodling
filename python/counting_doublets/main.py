import argparse
from glob import glob
import os
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from slcio import SlcioToHitsDataFrame
from timelapse import Timelapse
from doublet import DoubletMaker
from plot import Plotter
from constants import SIGNAL


FNAMES = [
    # neutrinoGun 100%, (-5, 15)
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15/neutrinoGun_digi_1.slcio",

    # neutrinoGun 10% (-5, 15)
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15_0.10/neutrinoGun_digi_1.slcio",

    # neutrinoGun 100%
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun/neutrinoGun_digi_1.slcio",

    # neutrinoGun 10%
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_0.10/neutrinoGun_digi_1.slcio",

    # muonGun
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_300.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_301.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_302.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_303.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_304.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_305.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_306.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_307.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_308.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_309.slcio",
]


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    ops = options()
    fnames = get_filenames(ops.i)
    geometry = ops.geometry
    signal = any(SIGNAL in os.path.basename(fname) for fname in fnames)
    logger.info(f"Detected {'signal' if signal else 'background'} files")

    # convert slcio to hits dataframe
    converter = SlcioToHitsDataFrame(slcio_file_paths=fnames,
                                     load_geometry=geometry)
    mcps, simhits = converter.convert()

    # make doublets from hits
    doublets = DoubletMaker(signal=signal, simhits=simhits).df
    if not signal:
        # drop simhit_r_upper, ... for a speedup
        logger.info("Dropping simhit_{x,y,z}_{upper,lower} columns from doublets ...")
        doublets.drop(columns=[
            "simhit_r_upper",
            "simhit_r_lower",
            "simhit_x_upper",
            "simhit_x_lower",
            "simhit_y_upper",
            "simhit_y_lower",
            "simhit_z_upper",
            "simhit_z_lower",
        ], inplace=True)

    # plot stuff
    plotter = Plotter(
        signal=signal,
        mcps=mcps,
        simhits=simhits,
        doublets=doublets,
        pdf="doublets.pdf",
    )
    plotter.plot()

    # logger.info("Creating timelapse gif ...")
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
