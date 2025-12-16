import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

import pyLCIO
import dd4hep
import DDRec

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
FIRST_FEW_MODULES = [0, 1]
FIRST_FEW_SENSORS = [0, 1]

def main():

    # load geometry
    detector = dd4hep.Detector.getInstance()
    detector.fromCompact(XML)
    surfman = DDRec.SurfaceManager(detector)
    dets = {}
    dets["InnerTrackerBarrelCollection"] = detector.detector("InnerTrackerBarrel")
    dets["OuterTrackerBarrelCollection"] = detector.detector("OuterTrackerBarrel")
    maps = {}
    for name, det in dets.items():
        maps[name] = surfman.map(det.name())
        print(f"Number of surfaces in {name} map:", len(maps[name]))

    # converting id to physical quantities
    def convert_id(id: int) -> dict:
        return {
            "system": (id >> 0) & 0b1_1111,
            "side": (id >> 5) & 0b11,
            "layer": (id >> 7) & 0b11_1111,
            "module": (id >> 13) & 0b111_1111_1111,
            "sensor": (id >> 24) & 0b1111_1111,
        }

    # storage
    corners_xy = {}
    corners_rz = {}

    # find a bounding box for each surface
    for name, surf_map in maps.items():

        for i_pair, surf_pair in enumerate(surf_map):

            if i_pair % 1000 == 0:
                print(f"Processing surface {i_pair} / {len(surf_map)} in {name}...")
            # if i_pair > 200:
            #     break

            id = surf_pair.first
            # print(f"{name} {i_pair} id: {id:010x}")
            surf = surf_pair.second
            origin = surf.origin()
            udir = surf.u()
            vdir = surf.v()
            ndir = surf.normal()
            len_u = surf.length_along_u()
            len_v = surf.length_along_v()
            len_n = surf.innerThickness()

            half_u = dd4hep.rec.Vector3D(
                udir.x() * len_u / 2.0,
                udir.y() * len_u / 2.0,
                udir.z() * len_u / 2.0,
            )
            half_v = dd4hep.rec.Vector3D(
                vdir.x() * len_v / 2.0,
                vdir.y() * len_v / 2.0,
                vdir.z() * len_v / 2.0,
            )
            half_n = dd4hep.rec.Vector3D(
                ndir.x() * len_n / 2.0,
                ndir.y() * len_n / 2.0,
                ndir.z() * len_n / 2.0,
            )

            corners_xy[id] = [
                origin - half_u - half_n,
                origin - half_u + half_n,
                origin + half_u + half_n,
                origin + half_u - half_n,
            ]
            corners_rz[id] = [
                origin - half_v - half_n,
                origin - half_v + half_n,
                origin + half_v + half_n,
                origin + half_v - half_n,
            ]

            # print("")
            # print("innerThickness:", surf.innerThickness())
            # print("outerThickness:", surf.outerThickness())
            # print("origin:", origin.x(), origin.y(), origin.z())
            # print("udir:", udir.x(), udir.y(), udir.z())
            # print("vdir:", vdir.x(), vdir.y(), vdir.z())
            # print("ndir:", ndir.x(), ndir.y(), ndir.z())
            # for corner in corners_xy[-1]:
            #     print("  corner_xy:", corner.x(), corner.y(), corner.z())
            # for corner in corners_rz[-1]:
            #     print("  corner_rz:", corner.x(), corner.y(), corner.z())
            # print("")


    fname = f"surface_bounds.pdf"
    print(f"Writing bounding box to {fname}...")
    with PdfPages(fname) as pdf:

        fig, ax = plt.subplots(figsize=(8,8))
        for it, (id, c_xy) in enumerate(corners_xy.items()):
            if it % 1000 == 0:
                print(f"Plotting surface {it} / {len(corners_xy)}...")
            if convert_id(id)["sensor"] not in FIRST_FEW_SENSORS:
                continue
            ax.scatter(
                [c.x() for c in c_xy],
                [c.y() for c in c_xy],
                color="blue",
                s=0.1,
            )
            rect_xy = plt.Polygon(
                [(c.x(), c.y()) for c in c_xy],
                fill="blue",
                edgecolor="blue",
            )
            ax.add_patch(rect_xy)
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots(figsize=(8,8))
        for it, (id, c_rz) in enumerate(corners_rz.items()):
            if it % 1000 == 0:
                print(f"Plotting surface {it} / {len(corners_rz)}...")
            if convert_id(id)["module"] not in FIRST_FEW_MODULES:
                continue
            ax.scatter(
                [c.z() for c in c_rz],
                [np.sqrt(c.x()**2 + c.y()**2) for c in c_rz],
                color="red",
                s=0.1,
            )
            rect_rz = plt.Polygon(
                [(c.z(), np.sqrt(c.x()**2 + c.y()**2)) for c in c_rz],
                fill="red",
                edgecolor="red",
            )
            ax.add_patch(rect_rz)
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Z [mm]")
        ax.set_ylabel("R [mm]")
        # ax.set_title(f"Surface ID {id} in {name}")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


if __name__ == "__main__":
    main()
