import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

import pyLCIO
import dd4hep
import DDRec

PARQUET = "geometry.parquet"
PDF = "geometry.pdf"
CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
FIRST_FEW_MODULES = [0, 1]
FIRST_FEW_SENSORS = [0, 1]
CM_TO_MM = 10.0


def main():
    corners_xy, corners_rz = read_geometry()
    plot(corners_xy, corners_rz)


def read_geometry():

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

    # storage
    rows = []
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

            rows.append({
                "id": id,
                **convert_id(id),
                "origin_x": origin.x() * CM_TO_MM,
                "origin_y": origin.y() * CM_TO_MM,
                "origin_z": origin.z() * CM_TO_MM,
                "corner_xy_0_x": corners_xy[id][0].x() * CM_TO_MM,
                "corner_xy_0_y": corners_xy[id][0].y() * CM_TO_MM,
                "corner_xy_0_z": corners_xy[id][0].z() * CM_TO_MM,
                "corner_xy_1_x": corners_xy[id][1].x() * CM_TO_MM,
                "corner_xy_1_y": corners_xy[id][1].y() * CM_TO_MM,
                "corner_xy_1_z": corners_xy[id][1].z() * CM_TO_MM,
                "corner_xy_2_x": corners_xy[id][2].x() * CM_TO_MM,
                "corner_xy_2_y": corners_xy[id][2].y() * CM_TO_MM,
                "corner_xy_2_z": corners_xy[id][2].z() * CM_TO_MM,
                "corner_xy_3_x": corners_xy[id][3].x() * CM_TO_MM,
                "corner_xy_3_y": corners_xy[id][3].y() * CM_TO_MM,
                "corner_xy_3_z": corners_xy[id][3].z() * CM_TO_MM,
                "corner_rz_0_x": corners_rz[id][0].x() * CM_TO_MM,
                "corner_rz_0_y": corners_rz[id][0].y() * CM_TO_MM,
                "corner_rz_0_z": corners_rz[id][0].z() * CM_TO_MM,
                "corner_rz_1_x": corners_rz[id][1].x() * CM_TO_MM,
                "corner_rz_1_y": corners_rz[id][1].y() * CM_TO_MM,
                "corner_rz_1_z": corners_rz[id][1].z() * CM_TO_MM,
                "corner_rz_2_x": corners_rz[id][2].x() * CM_TO_MM,
                "corner_rz_2_y": corners_rz[id][2].y() * CM_TO_MM,
                "corner_rz_2_z": corners_rz[id][2].z() * CM_TO_MM,
                "corner_rz_3_x": corners_rz[id][3].x() * CM_TO_MM,
                "corner_rz_3_y": corners_rz[id][3].y() * CM_TO_MM,
                "corner_rz_3_z": corners_rz[id][3].z() * CM_TO_MM,
            })

    # write dataframe to file
    df = pd.DataFrame(rows)
    print(df)
    print(f"Writing geometry data frame to {PARQUET}...")
    df.to_parquet(PARQUET)

    return corners_xy, corners_rz

def plot(corners_xy: dict, corners_rz: dict):

    print(f"Writing bounding box to {PDF}...")
    with PdfPages(PDF) as pdf:

        fig, ax = plt.subplots(figsize=(8,8))
        for it, (id, c_xy) in enumerate(corners_xy.items()):
            if it % 1000 == 0:
                print(f"Plotting surface {it} / {len(corners_xy)}...")
            if convert_id(id)["sensor"] not in FIRST_FEW_SENSORS:
                continue
            ax.scatter(
                [c.x() * CM_TO_MM for c in c_xy],
                [c.y() * CM_TO_MM for c in c_xy],
                color="blue",
                s=0.1,
            )
            rect_xy = plt.Polygon(
                [(c.x() * CM_TO_MM,
                  c.y() * CM_TO_MM) for c in c_xy],
                fill="blue",
                edgecolor="blue",
            )
            ax.add_patch(rect_xy)
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
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
                [c.z() * CM_TO_MM for c in c_rz],
                [np.sqrt((c.x() * CM_TO_MM)**2 + (c.y() * CM_TO_MM)**2) for c in c_rz],
                color="red",
                s=0.1,
            )
            rect_rz = plt.Polygon(
                [(c.z() * CM_TO_MM,
                  np.sqrt((c.x() * CM_TO_MM)**2 + (c.y() * CM_TO_MM)**2)) for c in c_rz],
                fill="red",
                edgecolor="red",
            )
            ax.add_patch(rect_rz)
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("z [mm]")
        ax.set_ylabel("r [mm]")
        # ax.set_title(f"Surface ID {id} in {name}")
        ax.minorticks_on()
        ax.grid(which="both")
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


def convert_id(id: int) -> dict:
    return {
        "system": (id >> 0) & 0b1_1111,
        "side": (id >> 5) & 0b11,
        "layer": (id >> 7) & 0b11_1111,
        "module": (id >> 13) & 0b111_1111_1111,
        "sensor": (id >> 24) & 0b1111_1111,
    }



if __name__ == "__main__":
    main()
