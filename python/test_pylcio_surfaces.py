"""
Following the example of:
https://github.com/iLCSoft/MarlinTrkProcessors/blob/master/source/Digitisers/src/DDPlanarDigiProcessor.cc
"""""
import pyLCIO
import dd4hep
import DDRec

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2025_12_05_12h49m00s/m5000p5000_timing_cuts_166.neutrinoGun_digi_100.slcio"
COLLECTION = "InnerTrackerBarrelCollection"


def main():
    detector = dd4hep.Detector.getInstance()
    detector.fromCompact(XML)
    print("detector:", detector)

    det = detector.detector("InnerTrackerBarrel")
    print("det:", det)

    # surf_man = dd4hep.SurfaceManager.getInstance()
    # surf_man2 = detector.extensions().get("SurfaceManager")
    # surfMan = det.extension(dd4hep.rec.SurfaceManager)
    # print("surfMan:", surfMan)
    surfMan = DDRec.SurfaceManager(detector)
    print(type(surfMan))
    print(surfMan.toString())
    _map = surfMan.map(det.name())
    print("Number of surfaces in map:", len(_map))


    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(SLCIO)
    for i_event, event in enumerate(reader):
        print(f"Event number: {event.getEventNumber()}")
        for name in sorted(list(event.getCollectionNames())):
            print(name)
        collection = event.getCollection(COLLECTION)
        print(f"Collection: {COLLECTION}, Number of elements: {len(collection)}")

        inside, outside = 0, 0

        for i_hit, hit in enumerate(collection):

            if i_hit % 2e5 == 0:
                print(f" Processing hit {i_hit}")

            # pos = hit.getPosition()
            # print(f" Hit {i_hit}: x={pos[0]:.2f}, y={pos[1]:.2f}, z={pos[2]:.2f}, t={hit.getTime():.2f} ns, EDep={hit.getEDep():.2f} MeV")

            cellid0 = hit.getCellID0()
            # print(f" CellID0: {cellid0:08x}")
            # print("_map", _map)
            # print("_map type:", type(_map))
            # print("_map len:", len(_map))
            # print("_map.find(cellid0)", _map.find(cellid0))
            # print("_map.find(cellid0).second", _map.find(cellid0).second)
            surf = _map.find(cellid0).second

            pos = dd4hep.rec.Vector3D(hit.getPosition()[0],
                                      hit.getPosition()[1],
                                      hit.getPosition()[2])

            if surf.insideBounds(pos):
                inside += 1
            else:
                outside += 1

            # print("pos:", pos)
            if i_hit < 100:
                inside_ = surf.insideBounds(pos)
                distance = int(surf.distance(pos))
                hit_x, hit_y, hit_z = int(pos.x()), int(pos.y()), int(pos.z())
                origin_x, origin_y, origin_z = int(surf.origin().x()), int(surf.origin().y()), int(surf.origin().z())
                print(f"{inside_=}, {distance=}, {hit_x=}, {hit_y=}, {hit_z=}, {origin_x=}, {origin_y=}, {origin_z=}")

            # print("_map.get(cellid0):", _map.get(cellid0))
            # print("_map.at(cellid0):", _map.at(cellid0))

        print(f" Total hits: {len(collection)}, inside bounds: {inside}, outside bounds: {outside}")
        break  # just first event


if __name__ == "__main__":
    main()


