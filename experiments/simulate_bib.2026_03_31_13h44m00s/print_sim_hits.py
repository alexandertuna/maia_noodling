import argparse
import contextlib
import os
import sys
import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({
    "font.size": 16,
    "figure.figsize": (8, 8),
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "axes.grid": True,
    "axes.grid.which": "both",
    # "axes.axisbelow": True,
    "grid.linewidth": 0.5,
    "grid.alpha": 0.1,
    "grid.color": "gray",
    "figure.subplot.left": 0.15,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

import pyLCIO
import dd4hep, DDRec

INNER_TRACKER_BARREL_COLLECTION = "InnerTrackerBarrelCollection"
OUTER_TRACKER_BARREL_COLLECTION = "OuterTrackerBarrelCollection"
GEV_TO_KEV = 1e6
MM_TO_CM = 0.1
CM_TO_MM = 10.0

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    ops = options()
    num_hits = ops.num_hits
    if not os.path.exists(ops.input):
        raise FileNotFoundError(f"Input file not found: {ops.input}")

    # Load the detector
    dd4hep.setPrintLevel(dd4hep.PrintLevel.WARNING)
    with silence_c_stdout_stderr():
        # Sorry for this context manager. dd4hep can be very noisy
        detector = dd4hep.Detector.getInstance()
        detector.fromCompact(XML)
        surfman = DDRec.SurfaceManager(detector)
        dets = {
            INNER_TRACKER_BARREL_COLLECTION: detector.detector("InnerTrackerBarrel"),
            OUTER_TRACKER_BARREL_COLLECTION: detector.detector("OuterTrackerBarrel"),
        }
        maps = {name: surfman.map(det.name()) for name, det in dets.items()}


    # Open the slcio file
    logger.info(f"Opening file: {ops.input}")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(ops.input)

    # Record some info about hits
    hits = []

    # For each event, print the number of sim hits in the tracker
    with open(ops.output, "w") as fi:
        for i, event in enumerate(reader):
            col = event.getCollection(INNER_TRACKER_BARREL_COLLECTION)
            logger.info(f"Event {i}: {col.getNumberOfElements():_} sim hits")
            # Print the first num_hits sim hits
            for i_hit, hit in enumerate(col):
                if num_hits >= 0 and i_hit >= num_hits:
                    break
                hit_e = hit.getEDep() * GEV_TO_KEV
                if hit_e < ops.emin:
                    continue
                hit_pathlength = hit.getPathLength()
                hit_t = hit.getTime()
                hit_x = hit.getPosition()[0]
                hit_y = hit.getPosition()[1]
                hit_z = hit.getPosition()[2]
                hit_r = (hit_x**2 + hit_y**2)**0.5
                hit_cellid0 = hit.getCellID0()

                surf = maps[INNER_TRACKER_BARREL_COLLECTION].find(hit.getCellID0()).second
                pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                          hit.getPosition()[1] * MM_TO_CM,
                                          hit.getPosition()[2] * MM_TO_CM)
                mom = dd4hep.rec.Vector3D(hit.getMomentum()[0],
                                          hit.getMomentum()[1],
                                          hit.getMomentum()[2])
                cos_theta = (mom * surf.normal()) / (mom.r() * surf.normal().r())
                inside_bounds = surf.insideBounds(pos)
                local = surf.globalToLocal(pos)
                local_u, local_v = local[0], local[1]
                origin_x, origin_y, origin_z = surf.origin()[0] * CM_TO_MM, surf.origin()[1] * CM_TO_MM, surf.origin()[2] * CM_TO_MM
                inner_thickness, outer_thickness = surf.innerThickness() * CM_TO_MM, surf.outerThickness() * CM_TO_MM

                u_norm = dd4hep.rec.Vector2D(1.0, 0.0)
                v_norm = dd4hep.rec.Vector2D(0.0, 1.0)
                u_len = surf.length_along_u()
                v_len = surf.length_along_v()
                u_vec = surf.localToGlobal(dd4hep.rec.Vector2D(u_norm[0] * u_len / 2.0,
                                                               u_norm[1] * u_len / 2.0))
                v_vec = surf.localToGlobal(dd4hep.rec.Vector2D(v_norm[0] * v_len / 2.0,
                                                               v_norm[1] * v_len / 2.0))

                outer_surface = dd4hep.rec.Vector3D(surf.normal()[0] * surf.outerThickness(),
                                                    surf.normal()[1] * surf.outerThickness(),
                                                    surf.normal()[2] * surf.outerThickness())
                inner_surface = dd4hep.rec.Vector3D(surf.normal()[0] * surf.innerThickness(),
                                                    surf.normal()[1] * surf.innerThickness(),
                                                    surf.normal()[2] * surf.innerThickness())

                outer_corner_0 = surf.origin() + outer_surface + u_vec + v_vec
                outer_corner_1 = surf.origin() + outer_surface + u_vec - v_vec
                outer_corner_2 = surf.origin() + outer_surface - u_vec + v_vec
                outer_corner_3 = surf.origin() + outer_surface - u_vec - v_vec
                inner_corner_0 = surf.origin() - inner_surface + u_vec + v_vec
                inner_corner_1 = surf.origin() - inner_surface + u_vec - v_vec
                inner_corner_2 = surf.origin() - inner_surface - u_vec + v_vec
                inner_corner_3 = surf.origin() - inner_surface - u_vec - v_vec
                distance = surf.distance(pos) * CM_TO_MM
                d_byhand = (pos - surf.origin()) *  surf.normal() * CM_TO_MM
                hits.append({
                    "local_u": local_u,
                    "local_v": local_v,
                    "inside_bounds": inside_bounds,
                    "pathlength": hit_pathlength,
                    "distance": distance,
                    "cos_theta": cos_theta,
                    "origin_x": origin_x,
                    "origin_y": origin_y,
                    "origin_z": origin_z,
                    "inner_thickness": inner_thickness,
                    "outer_thickness": outer_thickness,
                    "u_len": u_len,
                    "v_len": v_len,
                })

                # msg = f"Sim hit {i_hit}: 
                msg = (f"E={hit_e:5.2f} keV, pl={hit_pathlength:.3f}mm, time={hit_t:6.0f} ns, "
                       f"position=({hit_x:4.0f}, {hit_y:4.0f}, {hit_z:4.0f}) -> r={hit_r:4.0f}, "
                       f"cellID0={hit_cellid0:08x}, "
                       f"local=({local_u:.2f}, {local_v:.2f}), "
                       f"inside={inside_bounds}, d={distance:.3f}mm, d_={d_byhand:.3f}mm, cos_theta={cos_theta:.3f}"
                       )
                # logger.info(msg)
                fi.write(msg + "\n")

    df = pd.DataFrame(hits)
    df["inside_bounds"] = df["inside_bounds"].astype(bool)
    with PdfPages("sim_hits.pdf") as pdf:
        print(df)
        plot(df, pdf)


def plot(df: pd.DataFrame, pdf: PdfPages) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(df["local_u"], df["local_v"], c=df["inside_bounds"], cmap="coolwarm", s=10)
    ax.set_xlabel("local_u (mm)")
    ax.set_ylabel("local_v (mm)")
    ax.set_title("Sim hit local positions colored by inside_bounds")
    pdf.savefig()
    plt.close()



def options():
    parser = argparse.ArgumentParser(description="Print sim hits from a given slcio file.")
    parser.add_argument("-i", "--input", type=str, required=True,
                        help="Path to the input slcio file.")
    parser.add_argument("-n", "--num-hits", type=int, default=20,
                        help="Number of sim hits to print per event.")
    parser.add_argument("-e", "--emin", type=float, default=0.0,
                        help="Minimum energy of sim hits to print (keV).")
    parser.add_argument("-o", "--output", type=str, default="sim_hits.txt",
                        help="Path to the output text file.")
    return parser.parse_args()


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
