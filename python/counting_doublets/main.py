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
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15/neutrinoGun_digi_3.slcio",

    # neutrinoGun 10% (-5, 15)
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15_0.10/neutrinoGun_digi_3.slcio",

    # neutrinoGun 100%
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun/neutrinoGun_digi_1.slcio",

    # neutrinoGun 10%
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_0.10/neutrinoGun_digi_1.slcio",

    # muonGun, 0-10 GeV
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_300.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_301.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_302.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_303.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_304.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_305.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_306.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_307.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_308.slcio",
    # "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_309.slcio",

    # muonGun, 2 GeV
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_300.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_301.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_302.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_303.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_304.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_305.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_306.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_307.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_308.slcio",
    "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_309.slcio",
]


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    ops = options()
    fnames = get_filenames(ops.i)
    geometry = ops.geometry
    signal = any(SIGNAL in os.path.basename(fname) for fname in fnames)
    if not ops.inner and not ops.outer:
        raise ValueError("At least one of --inner or --outer must be specified")
    logger.info(f"Detected {'signal' if signal else 'background'} files")
    logger.info(f"Found {len(fnames)} files")
    logger.info(f"Inner tracker: {ops.inner}")
    logger.info(f"Outer tracker: {ops.outer}")
    logger.info(f"Layers to consider: {ops.layers}")
    logger.info(f"Cut doublets: {ops.cut_doublets}")

    # convert slcio to hits dataframe
    converter = SlcioToHitsDataFrame(slcio_file_paths=fnames,
                                     load_geometry=geometry,
                                     signal=signal,
                                     inner=ops.inner,
                                     outer=ops.outer,
                                     layers=ops.layers,
                                     )
    mcps, simhits = converter.convert()

    # make doublets from hits
    doublets = DoubletMaker(
        signal=signal,
        cut_doublets=ops.cut_doublets,
        simhits=simhits,
    ).df

    # plot stuff
    logger.info("Creating plots ...")
    plotter = Plotter(
        signal=signal,
        mcps=mcps,
        simhits=simhits,
        doublets=doublets,
        pdf="doublets.pdf",
    )
    plotter.plot()

    if ops.timelapse:
        logger.info("Creating timelapse gif ...")
        tl = Timelapse(df=simhits, event=0, gif="event.gif")


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", default=FNAMES, help="Input slcio file or glob pattern")
    parser.add_argument("--layers", nargs="+", type=int, default=[0, 1], help="List of numbers (default: [0, 1])")
    parser.add_argument("--geometry", action="store_true", help="Load compact geometry from xml")
    parser.add_argument("--timelapse", action="store_true", help="Create timelapse gif")
    parser.add_argument("--inner", action="store_true", help="Include inner tracker hits in the analysis")
    parser.add_argument("--outer", action="store_true", help="Include outer tracker hits in the analysis")
    parser.add_argument("--cut-doublets", action="store_true", help="Cut doublets based on DZ_CUT and DR_CUT")
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
