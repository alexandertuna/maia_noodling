import argparse
from glob import glob
import logging
logger = logging.getLogger(__name__)

from slcio import HitMaker
from doublet import DoubletMaker


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    # command line args
    ops = options()
    if not ops.signal and not ops.background10 and not ops.background100:
        raise ValueError("At least one of --signal, --background10 or --background100 must be specified")
    fnames = []
    if ops.signal:
        fnames.extend(signal_filenames())
    if ops.background10:
        fnames.extend(background_10p_filenames())
    if ops.background100:
        fnames.extend(background_100p_filenames())
    logger.info(f"Detected {'signal' if ops.signal else 'background'} files")
    logger.info(f"Found {len(fnames)} files")
    logger.info(f"Cut doublets: {ops.cut}")

    # convert slcio to hits dataframe
    simhits = HitMaker(signal=ops.signal, slcio_file_paths=fnames).df

    # make doublets from hits
    doublets = DoubletMaker(signal=ops.signal, cut=ops.cut, simhits=simhits).df


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--signal", action="store_true", help="Include signal files in the analysis")
    parser.add_argument("--background10", action="store_true", help="Include 10% background files in the analysis")
    parser.add_argument("--background100", action="store_true", help="Include 100% background files in the analysis")   
    parser.add_argument("--cut", action="store_true", help="Cut doublets based on DZ_CUT and DR_CUT")
    return parser.parse_args()


def get_filenames(fnames):
    names = []
    if isinstance(fnames, str):
        fnames = [fnames]
    for fname in fnames:
        names.extend(glob(fname))
    return names


def signal_filenames():
    return [
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


def background_10p_filenames():
    return [
        "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15_0.10/neutrinoGun_digi_3.slcio",
    ]


def background_100p_filenames():
    return [
        "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/neutrinoGun_n5_p15/neutrinoGun_digi_3.slcio",
    ]


if __name__ == "__main__":
    main()
