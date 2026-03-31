import argparse
import contextlib
import os
import sys
import logging
logger = logging.getLogger(__name__)

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
                inside_bounds = surf.insideBounds(pos)
                distance = surf.distance(pos) * CM_TO_MM

                # msg = f"Sim hit {i_hit}: 
                msg = (f"E={hit_e:5.2f} keV, pl={hit_pathlength:.3f}mm, time={hit_t:6.0f} ns, "
                       f"position=({hit_x:4.0f}, {hit_y:4.0f}, {hit_z:4.0f}) -> r={hit_r:4.0f}, "
                       f"cellID0={hit_cellid0:08x}, "
                       f"inside={inside_bounds}, d={distance:.3f}mm"
                       )
                # logger.info(msg)
                fi.write(msg + "\n")


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
