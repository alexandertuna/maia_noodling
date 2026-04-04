"""
Following the example of:
https://github.com/iLCSoft/MarlinTrkProcessors/blob/master/source/Digitisers/src/DDPlanarDigiProcessor.cc
"""""
import os, sys
import numpy as np
import pandas as pd
import contextlib

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geoMain/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
SLCIO = f"{CODE}/maia_noodling/experiments/simulate_bib.2026_03_31_13h44m00s/nuGun_filtered_0_30.slcio"
COLLECTION = [
    "VertexBarrelCollection",
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
MM_TO_CM = 0.1
MM_TO_UM = 1e3
CM_TO_UM = 1e4
CM_TO_MM = 10.0
SPEED_OF_LIGHT = 299.792458  # mm/ns
TIMEWINDOWMIN = -0.09
TIMEWINDOWMAX = 0.15
TIMEWINDOW = True


def main():
    parse_slcio()


def parse_slcio():

    print(f"Parsing {SLCIO}")

    # setup the detector quietly
    with silence_c_stdout_stderr():
        import pyLCIO
        import dd4hep
        import DDRec
        dd4hep.setPrintLevel(dd4hep.PrintLevel.WARNING)
        detector = dd4hep.Detector.getInstance()
        detector.fromCompact(XML)
        det = {collection: detector.detector(collection.replace("Collection", "")) for collection in COLLECTION}
        surfman = DDRec.SurfaceManager(detector)
        surfmap = {collection: surfman.map(det[collection].name()) for collection in COLLECTION}

    # counters
    total_hits = {collection: 0 for collection in COLLECTION}
    inside = {collection: 0 for collection in COLLECTION}
    outside = {collection: 0 for collection in COLLECTION}
    times = []

    # load the file
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(SLCIO)

    # event loop
    for i_event, event in enumerate(reader):

        # hit loop
        for collection_name in COLLECTION:

            collection = event.getCollection(collection_name)
            n_hit = len(collection)
            total_hits[collection_name] += n_hit

            for i_hit, hit in enumerate(collection):

                if i_hit % 1e6 == 0:
                    print(f" Processing {collection_name} hit {i_hit} / {n_hit}")

                # hit/surface relations
                cellid0 = hit.getCellID0()
                surf = surfmap[collection_name].find(cellid0).second
                pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                          hit.getPosition()[1] * MM_TO_CM,
                                          hit.getPosition()[2] * MM_TO_CM)
                inside_bounds = surf.insideBounds(pos)
                distance = surf.distance(pos) * CM_TO_UM

                # position corrected by speed of light
                corrected_time = hit.getTime() - (np.sqrt(hit.getPosition()[0]**2 + \
                                                          hit.getPosition()[1]**2 + \
                                                          hit.getPosition()[2]**2) / SPEED_OF_LIGHT)
                if TIMEWINDOW and (corrected_time < TIMEWINDOWMIN or corrected_time > TIMEWINDOWMAX):
                    total_hits[collection_name] -= 1
                    continue
                times.append(corrected_time)

                if inside_bounds:
                    inside[collection_name] += 1
                else:
                    outside[collection_name] += 1

    # describe the timing distribution
    times = pd.Series(times)
    print(f"Timing distribution: mean={times.mean():.2f} ns, std={times.std():.2f} ns, min={times.min():.2f} ns, max={times.max():.2f} ns")

    # announce
    width = max(len(collection) for collection in COLLECTION)
    percent_inside = {collection: inside[collection] / total_hits[collection] * 100 for collection in COLLECTION}
    percent_outside = {collection: outside[collection] / total_hits[collection] * 100 for collection in COLLECTION}
    for collection in COLLECTION:
        tot = total_hits[collection]
        n_in, n_out = inside[collection], outside[collection]
        p_in, p_out = percent_inside[collection], percent_outside[collection]
        print(f"{collection:>{width}}: Total hits {tot}, inside bounds {n_in} ({p_in:.0f}%), outside bounds {n_out} ({p_out:.0f}%)")


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


