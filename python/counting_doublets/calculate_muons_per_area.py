"""
Run me like:
> python calculate_muons_per_area.py --outer --layers 0
"""
import argparse
import os
import sys
import contextlib
import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from slcio import SlcioToHitsDataFrame
from constants import XML, CM_TO_MM
from constants import MUON, ONE_POINT_FIVE_GEV, ZERO_POINT_ZERO_ONE_MM, BARREL_TRACKER_MAX_ETA
from constants import INNER_TRACKER_BARREL, OUTER_TRACKER_BARREL, NICKNAMES

FNAMES = [
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
    fnames = FNAMES
    geometry = ops.geometry
    signal = True
    if not ops.inner and not ops.outer:
        raise ValueError("At least one of --inner or --outer must be specified")
    logger.info(f"Found {len(fnames)} files")
    logger.info(f"Inner tracker: {ops.inner}")
    logger.info(f"Outer tracker: {ops.outer}")
    logger.info(f"Layers to consider: {ops.layers}")

    # configure inner/outer tracker situation
    detnames = []
    if ops.inner:
        detnames.append("InnerTrackerBarrel")
    if ops.outer:
        detnames.append("OuterTrackerBarrel")
    detids = []
    if ops.inner:
        detids.append(INNER_TRACKER_BARREL)
    if ops.outer:
        detids.append(OUTER_TRACKER_BARREL)

    # get detector areas
    logger.info("Getting detector elements ...")
    elements = get_detector_elements(detnames)
    print(elements.head())

    # convert slcio to hits dataframe
    converter = SlcioToHitsDataFrame(slcio_file_paths=fnames,
                                     load_geometry=geometry,
                                     signal=signal,
                                     inner=ops.inner,
                                     outer=ops.outer,
                                     layers=ops.layers,
                                     )
    mcps, _ = converter.convert()

    # count number of muons
    mask = (
        (np.abs(mcps["mcp_pdg"]) == MUON) &
        (mcps["mcp_q"] != 0) &
        (mcps["mcp_pt"] > ONE_POINT_FIVE_GEV) &
        (mcps["mcp_vertex_r"] < ZERO_POINT_ZERO_ONE_MM) &
        (np.abs(mcps["mcp_vertex_z"]) < ZERO_POINT_ZERO_ONE_MM) &
        (np.abs(mcps["mcp_eta"]) < BARREL_TRACKER_MAX_ETA)
    )
    nmuons = mask.sum()

    # count the relevant area
    for detid in detids:
        for layer in ops.layers:
            mask = (
                (elements["system"] == detid) &
                (elements["layer"] == layer) &
                (np.abs(elements["eta"]) < BARREL_TRACKER_MAX_ETA + 0.01)
            )
            eles = mask.sum()
            nickname = NICKNAMES[detid]
            # area = elements[mask]["area"].sum()
            logger.info(f"{nickname} layer {layer}: n(muons)={nmuons}, n(sensors)={eles}, muons per sensor={nmuons / eles:.1f}")


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", default=FNAMES, help="Input slcio file or glob pattern")
    parser.add_argument("--layers", nargs="+", type=int, default=[0, 1, 2, 3, 4, 5, 6, 7], help="List of layers to consider")
    parser.add_argument("--geometry", action="store_true", help="Load compact geometry from xml")
    parser.add_argument("--inner", action="store_true", help="Include inner tracker hits in the analysis")
    parser.add_argument("--outer", action="store_true", help="Include outer tracker hits in the analysis")
    return parser.parse_args()


def get_detector_elements(detnames: list[str]) -> pd.DataFrame:
    import dd4hep, DDRec
    dd4hep.setPrintLevel(dd4hep.PrintLevel.WARNING)
    with silence_c_stdout_stderr():
        # Sorry for this context manager. dd4hep can be very noisy
        detector = dd4hep.Detector.getInstance()
        detector.fromCompact(XML)
        surfman = DDRec.SurfaceManager(detector)
        maps = [surfman.map(detname) for detname in detnames]
    rows = []
    for themap in maps:
        for it, (cellid0, surface) in enumerate(themap):
            origin = surface.origin()
            area = surface.length_along_u() * CM_TO_MM * surface.length_along_v() * CM_TO_MM
            rows.append({
                "system": np.right_shift(cellid0, 0) & 0b1_1111,
                "side": np.right_shift(cellid0, 5) & 0b11,
                "layer": np.right_shift(cellid0, 7) & 0b11_1111,
                "module": np.right_shift(cellid0, 13) & 0b111_1111_1111,
                "sensor": np.right_shift(cellid0, 24) & 0b1111_1111,
                "x": origin.x() * CM_TO_MM,
                "y": origin.y() * CM_TO_MM,
                "z": origin.z() * CM_TO_MM,
                "area": area,
            })

    df = pd.DataFrame(rows)
    df["r"] = np.sqrt(df["x"]**2 + df["y"]**2)
    df["theta"] = np.arctan2(df["r"], df["z"])
    df["eta"] = -np.log(np.tan(df["theta"] / 2))

    return df


@contextlib.contextmanager
def silence_c_stdout_stderr():
    # Flush Python buffers
    sys.stdout.flush()
    sys.stderr.flush()

    # Save original FDs
    old_stdout_fd = os.dup(1)
    old_stderr_fd = os.dup(2)

    # Redirect to /dev/null
    with open(os.devnull, "w") as devnull:
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            # Restore original FDs
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)


if __name__ == "__main__":
    main()
