"""
Following the example of:
https://github.com/iLCSoft/MarlinTrkProcessors/blob/master/source/Digitisers/src/DDPlanarDigiProcessor.cc
"""""

import pyLCIO
import dd4hep
import DDRec
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import colors
from matplotlib import rcParams
rcParams.update({"font.size": 16})

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2025_12_05_12h49m00s/m5000p5000_timing_cuts_166.neutrinoGun_digi_100.slcio"
COLLECTION = "InnerTrackerBarrelCollection"
MM_TO_CM = 0.1
CM_TO_UM = 1e4
CM_TO_MM = 10.0
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
    total_hits = 0
    inside, outside = 0, 0

    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(SLCIO)
    for i_event, event in enumerate(reader):
        print(f"Event number: {event.getEventNumber()}")
        for name in sorted(list(event.getCollectionNames())):
            print(name)
        collection = event.getCollection(COLLECTION)
        print(f"Collection: {COLLECTION}, Number of elements: {len(collection)}")
        total_hits += len(collection)

        for i_hit, hit in enumerate(collection):

            if i_hit % 2e5 == 0:
                print(f" Processing hit {i_hit}")

            cellid0 = hit.getCellID0()
            energy = hit.getEDep() * GEV_TO_KEV
            time = hit.getTime()
            path_length = hit.getPathLength()
            surf = _map.find(cellid0).second
            pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                      hit.getPosition()[1] * MM_TO_CM,
                                      hit.getPosition()[2] * MM_TO_CM)
            mom = dd4hep.rec.Vector3D(hit.getMomentum()[0],
                                      hit.getMomentum()[1],
                                      hit.getMomentum()[2])
            inside_bounds = surf.insideBounds(pos)
            distance = surf.distance(pos) * CM_TO_UM
            local = surf.globalToLocal(pos)
            cos_theta = (mom * surf.normal()) / (mom.r() * surf.normal().r())

            if i_hit == 0:
                print(f" Surface origin: {surf.origin()}")
                print(f" Hit position: {pos}")
                print(f" Local position: {local}")
                print(f" Distance to surface: {distance} um")
                print(f" Inside bounds: {inside_bounds}")
                print(f" Surface type: {type(surf)}")
                print(f" Surface type: {surf.type()}")
                print(f" Surface isSensitive: {surf.type().isSensitive()}")
                print(f" Surface isHelper: {surf.type().isHelper()}")
                print(f" Surface isPlane: {surf.type().isPlane()}")
                print(f" Surface isCylinder: {surf.type().isCylinder()}")
                print(f" Surface isCone: {surf.type().isCone()}")
                print(f" Surface isVisible: {surf.type().isVisible()}")
                print(f" Surface isUnbounded: {surf.type().isUnbounded()}")
                # return

            """
            double VolPlaneImpl::distance(const Vector3D& point ) const {
              return ( point - origin() ) *  normal()  ;
            }
            """
            if i_hit < 50:
                my_distance_0 = surf.distance(pos)
                my_distance_1 = (pos - surf.origin()) * surf.normal()
                diff = pos - surf.origin()
                str_pos = f"({pos.x():6.2f}, {pos.y():6.2f}, {pos.z():6.2f})"
                str_origin = f"({surf.origin().x():6.2f}, {surf.origin().y():6.2f}, {surf.origin().z():6.2f})"
                str_normal = f"({surf.normal().x():6.2f}, {surf.normal().y():6.2f}, {surf.normal().z():6.2f})"
                str_diff = f"({diff.x():6.2f}, {diff.y():6.2f}, {diff.z():6.2f})"
                str_distance = f"{my_distance_0:9.5f} vs {my_distance_1:9.5f} -> isclose: {np.isclose(my_distance_0, my_distance_1)}"
                str_inside = f"inside: {inside_bounds}"
                str_theta = f"cos(theta): {cos_theta:6.4f}"
                print(f" Distance check: pos: {str_pos}, origin: {str_origin}, diff: {str_diff}, normal: {str_normal} => {str_distance}, {str_inside}, {str_theta} ")


            if i_hit < 100 and False:
                inside_ = inside_bounds
                hit_x, hit_y, hit_z = [int(pos.x() * CM_TO_MM),
                                       int(pos.y() * CM_TO_MM),
                                       int(pos.z() * CM_TO_MM),
                                       ]
                origin_x, origin_y, origin_z = [int(surf.origin().x() * CM_TO_MM),
                                                int(surf.origin().y() * CM_TO_MM),
                                                int(surf.origin().z() * CM_TO_MM),
                                               ]
                local_u, local_v = [int(local.u() * CM_TO_MM),
                                    int(local.v() * CM_TO_MM),
                                   ]
                print(f"{inside_=:5}, {distance=:6.2f}, {hit_x=:6}, {hit_y=:6}, {hit_z=:6}, {origin_x=:6}, {origin_y=:6}, {origin_z=:6}, {local_u=:6}, {local_v=:6}")
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
                "local_u": local.u() * CM_TO_MM,
                "local_v": local.v() * CM_TO_MM,
                "cos_theta": cos_theta,
                "path_length": path_length,
            })


    print(f" Total hits: {total_hits}, inside bounds: {inside}, outside bounds: {outside}")

    # create dataframe
    df = pd.DataFrame(hits)
    df["layer"] = np.right_shift(df["cellid0"], 7) & 0b11_1111

    # show some stats
    inside = df[df["inside_bounds"] == True]
    outside = df[df["inside_bounds"] == False]
    print(f"Inside bounds:")
    print(inside["abs_distance"].describe())
    print(f"Outside bounds:")
    print(outside["abs_distance"].describe())

    with PdfPages("test_pylcio_surfaces.pdf") as pdf:

        # distance
        print("Plotting distance to surface ...")
        fig, ax = plt.subplots(figsize=(8, 8))
        bins = np.linspace(-60, 60, 121)
        ax.hist(inside["distance"], bins=bins, alpha=0.5, label="Inside bounds")
        ax.hist(outside["distance"], bins=bins, alpha=0.5, label="Outside bounds")
        ax.set_xlabel("Distance to surface [um]")
        ax.set_ylabel("Counts")
        ax.set_title("Distance to surface for hits in InnerTrackerBarrel")
        ax.legend()
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()

        # cos theta
        print("Plotting cosine of incidence angle ...")
        fig, ax = plt.subplots(figsize=(8, 8))
        bins = np.linspace(-1, 1, 201)
        ax.hist(inside["cos_theta"], bins=bins, alpha=0.5, label="Inside bounds")
        ax.hist(outside["cos_theta"], bins=bins, alpha=0.5, label="Outside bounds")
        ax.set_xlabel("Cosine of incidence angle")
        ax.set_ylabel("Counts")
        ax.set_title("Incidence angle for hits in InnerTrackerBarrel")
        ax.legend()
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()

        # path length
        print("Plotting path length ...")
        for bins in [
            np.linspace(0, 1, 501),
            np.linspace(0, 10, 201),
        ]:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.hist(inside["path_length"], bins=bins, alpha=0.5, label="Inside bounds")
            ax.hist(outside["path_length"], bins=bins, alpha=0.5, label="Outside bounds")
            ax.set_xlabel("Path length [mm]")
            ax.set_ylabel("Counts")
            ax.set_title("Path length for hits in InnerTrackerBarrel")
            ax.legend()
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            ax.semilogy()
            pdf.savefig()
            plt.close()

        # distance vs cos theta
        print("Plotting distance vs incidence angle ...")
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            for norm in [None, colors.LogNorm()]:
                fig, ax = plt.subplots(figsize=(8, 8))
                bins = [np.linspace(-1, 1, 201),
                        np.linspace(-60, 60, 121),
                        ]
                # log-z scale
                _, _, _, im = ax.hist2d(
                        the_df["cos_theta"],
                        the_df["distance"],
                        bins=bins,
                        cmap="hot",
                        cmin=0.5,
                        norm=norm,
                        )
                fig.colorbar(im, ax=ax, pad=0.01, label="Counts")
                ax.set_xlabel("Cosine of incidence angle")
                ax.set_ylabel("Distance to surface [um]")
                ax.set_title(f"Distance vs incidence angle {tag} bounds")
                fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                pdf.savefig()
                plt.close()

        # local u vs v
        print("Plotting local u vs v ...")
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            fig, ax = plt.subplots(figsize=(8, 8))
            bins = [
                np.linspace(-24, 24, 241),
                np.linspace(-24, 24, 241),
            ]
            _, _, _, im = ax.hist2d(the_df["local_u"], the_df["local_v"], bins=bins, cmap="hot", cmin=0.5)
            ax.set_xlabel("Local u [mm]")
            ax.set_ylabel("Local v [mm]")
            ax.set_title(f"Local hit positions {tag} bounds")
            fig.colorbar(im, ax=ax, pad=0.01, label="Counts")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            plt.close()

        # local u vs v when abs(cos_theta) <XX vs >YY
        print("Plotting local u vs v with different incidence angles ...")
        cut_value_lt = 0.5
        cut_value_gt = 0.9
        bins = [
            np.linspace(-24, 24, 241),
            np.linspace(-24, 24, 241),
        ]
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            for scenario in [f"abs(cos(theta)) < {cut_value_lt}",
                             f"abs(cos(theta)) > {cut_value_gt}",
                             ]:
                mask = (
                    (abs(the_df["cos_theta"]) < cut_value_lt)
                    if ("<" in scenario) else
                    (abs(the_df["cos_theta"]) > cut_value_gt)
                )
                sel = the_df[mask]
                fig, ax = plt.subplots(figsize=(8, 8))
                _, _, _, im = ax.hist2d(
                    sel["local_u"],
                    sel["local_v"],
                    bins=bins,
                    cmap="hot",
                    cmin=0.5,
                )
                ax.set_xlabel("Local u [mm]")
                ax.set_ylabel("Local v [mm]")
                ax.set_title(f"Local hit positions {tag} bounds, {scenario}")
                fig.colorbar(im, ax=ax, pad=0.01, label="Counts")
                fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                pdf.savefig()
                plt.close()


if __name__ == "__main__":
    main()


