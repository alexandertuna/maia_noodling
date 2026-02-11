import contextlib
import os
import sys
import numpy as np
import pandas as pd
import time

FNAME = "tmp.slcio"
# FNAME = "outsideBounds_1_event.slcio"
TRACKER = "InnerTrackerBarrelCollection"
XML = "/ceph/users/atuna/work/maia/k4geoInsideBounds/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"

MM_TO_CM = 0.1
CM_TO_MM = 10.0

WEIRD_R_LO = 145
WEIRD_R_HI = 155


def main():

    hits = get_hits([FNAME])
    mask = (hits["r"] > WEIRD_R_LO) & (hits["r"] < WEIRD_R_HI)
    if mask.sum() == 0:
        print(len(mask), time.strftime("%Y_%m_%d_%Hh%Mm%Ss"))
        # print(hits)
        return
    else:
        with pd.option_context("display.min_rows", 100,
                               "display.max_rows", 100,
                               ):
            print(hits)
        sys.exit(-1)


def get_hits(fnames: list[str]) -> pd.DataFrame:

    hits = []

    with silence_c_stdout_stderr():
        import pyLCIO
        import dd4hep, DDRec
        dd4hep.setPrintLevel(dd4hep.PrintLevel.WARNING)
        # Sorry for this context manager. dd4hep can be very noisy
        _detector = dd4hep.Detector.getInstance()
        _detector.fromCompact(XML)
        _surfman = DDRec.SurfaceManager(_detector)
        dets = {
            "InnerTrackerBarrelCollection": _detector.detector("InnerTrackerBarrel"),
        }
        _maps = {name: _surfman.map(det.name()) for name, det in dets.items()}

    for fname in fnames:

        # print(f"Reading {fname} ...")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(fname)
    
        for i_event, event in enumerate(reader):

            col = event.getCollection(TRACKER)
            for i_hit, hit in enumerate(col):

                surf = _maps[TRACKER].find(hit.getCellID0()).second
                pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                          hit.getPosition()[1] * MM_TO_CM,
                                          hit.getPosition()[2] * MM_TO_CM)
                inside_bounds = surf.insideBounds(pos)

                hits.append( [
                    i_event,
                    hit.getPositionVec().X(),
                    hit.getPositionVec().Y(),
                    hit.getPositionVec().Z(),
                    hit.getMomentumVec().X(),
                    hit.getMomentumVec().Y(),
                    hit.getMomentumVec().Z(),
                    hit.getCellID0(),
                    hit.getPathLength(),
                    inside_bounds,
                ] )

    if len(hits) == 0:
        raise Exception("No hits found!")

    columns = ["event", "x", "y", "z", "px", "py", "pz", "cellid0", "pathlength", "insideBounds"]
    hits = pd.DataFrame(np.array(hits), columns=columns)
    hits["r"] = np.sqrt(hits["x"]**2 + hits["y"]**2)

    return hits


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
