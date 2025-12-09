"""
Following the example of:
https://github.com/iLCSoft/MarlinTrkProcessors/blob/master/source/Digitisers/src/DDPlanarDigiProcessor.cc
"""""

import pyLCIO
import dd4hep
import DDRec
import numpy as np
import pandas as pd

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2025_12_05_12h49m00s/m5000p5000_timing_cuts_166.neutrinoGun_digi_100.slcio"
COLLECTION = "InnerTrackerBarrelCollection"
MM_TO_CM = 0.1
CM_TO_UM = 1e4
GEV_TO_KEV = 1e6


def main():

    # setup the detector
    detector = dd4hep.Detector.getInstance()
    detector.fromCompact(XML)
    det = detector.detector("InnerTrackerBarrel")
    surfMan = DDRec.SurfaceManager(detector)
    _map = surfMan.map(det.name())
    print("Number of surfaces in map:", len(_map))

    # prepare for a dataframe
    hits = []
    inside, outside = 0, 0

    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(SLCIO)
    for i_event, event in enumerate(reader):
        print(f"Event number: {event.getEventNumber()}")
        for name in sorted(list(event.getCollectionNames())):
            print(name)
        collection = event.getCollection(COLLECTION)
        print(f"Collection: {COLLECTION}, Number of elements: {len(collection)}")


        for i_hit, hit in enumerate(collection):

            if i_hit % 2e5 == 0:
                print(f" Processing hit {i_hit}")

            cellid0 = hit.getCellID0()
            energy = hit.getEDep() * GEV_TO_KEV
            time = hit.getTime()
            surf = _map.find(cellid0).second
            pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                      hit.getPosition()[1] * MM_TO_CM,
                                      hit.getPosition()[2] * MM_TO_CM)
            inside_bounds = surf.insideBounds(pos)
            distance = surf.distance(pos) * CM_TO_UM

            if i_hit < 100:
                inside_ = inside_bounds
                hit_x, hit_y, hit_z = int(pos.x()), int(pos.y()), int(pos.z())
                origin_x, origin_y, origin_z = int(surf.origin().x()), int(surf.origin().y()), int(surf.origin().z())
                print(f"{inside_=:5}, {distance=:6.2f}, {hit_x=:6}, {hit_y=:6}, {hit_z=:6}, {origin_x=:6}, {origin_y=:6}, {origin_z=:6}, {energy=:.2f}, {time=:.2f}")

            if inside_bounds:
                inside += 1
            else:
                outside += 1

            hits.append({
                "collection": COLLECTION,
                "energy": energy,
                "time": time,
                "distance": distance,
                "abs_distance": abs(distance),
                "inside_bounds": inside_bounds,
                "cellid0": cellid0,
            })


    print(f" Total hits: {len(collection)}, inside bounds: {inside}, outside bounds: {outside}")

    # create dataframe
    df = pd.DataFrame(hits)
    df["layer"] = np.right_shift(df["cellid0"], 7) & 0b11_1111

    # show some stats
    for layer in sorted(df["layer"].unique()):
        inside = df[(df["layer"] == layer) & (df["inside_bounds"] == True)]
        outside = df[(df["layer"] == layer) & (df["inside_bounds"] == False)]
        print(f"Layer {layer}, inside bounds:")
        print(inside["abs_distance"].describe())
        print(f"Layer {layer}, outside bounds:")
        print(outside["abs_distance"].describe())


if __name__ == "__main__":
    main()


