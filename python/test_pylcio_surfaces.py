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
rcParams.update({
    "font.size": 16,
    "figure.figsize": (8, 8),
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
})

CODE = "/ceph/users/atuna/work/maia"
# XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
XML = f"{CODE}/k4geoMain/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"
# SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2025_12_05_12h49m00s/m5000p5000_timing_cuts_166.neutrinoGun_digi_100.slcio"
# SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2025_12_05_12h49m00s/neutrinoGun_sim_100.slcio"
# SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2026_01_07_22h00m00s/BIB10TeV/sim_mm/BIB_sim_100.slcio"
# SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2026_03_31_13h44m00s/2026_03_31_15h01m00s/BIB_sim.sim_EVENT_None.slcio"
SLCIO = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2026_03_31_13h44m00s/nuGun_filtered_0_30.slcio"
COLLECTION = "InnerTrackerBarrelCollection"
MCPARTICLE = "MCParticle"
MM_TO_CM = 0.1
MM_TO_UM = 1e3
CM_TO_UM = 1e4
CM_TO_MM = 10.0
GEV_TO_KEV = 1e6
EPSILON = 1e-4


def main():
    df = slcio_df()
    df = post_process(df)
    plot(df)


def slcio_df():

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

        if i_event == 0:
            print(" Collections in the event:")
            for name in sorted(list(event.getCollectionNames())):
                print(name)

        collection = event.getCollection(COLLECTION)
        mcps = [mcp for mcp in event.getCollection(MCPARTICLE)]
        print(f"Collection: {COLLECTION}, Number of elements: {len(collection)}")
        total_hits += len(collection)

        for i_hit, hit in enumerate(collection):

            if i_hit % 4e5 == 0:
                print(f" Processing hit {i_hit}")

            # sim hit info
            cellid0 = hit.getCellID0()
            energy = hit.getEDep() * GEV_TO_KEV
            time = hit.getTime()
            path_length = hit.getPathLength()
            if energy < 1.0: # keV
                continue

            # hit/surface relations
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
            origin_x = surf.origin().x() * CM_TO_MM
            origin_y = surf.origin().y() * CM_TO_MM
            origin_z = surf.origin().z() * CM_TO_MM
            normal_x = surf.normal().x() * CM_TO_MM
            normal_y = surf.normal().y() * CM_TO_MM
            normal_z = surf.normal().z() * CM_TO_MM

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

            # parent mc particle info
            mcp = hit.getMCParticle()
            i_mcp = mcps.index(mcp) if mcp else -1
            mc_pid = mcp.getPDG() if mcp else 0
            mc_e = mcp.getEnergy() if mcp else 0
            mc_px = mcp.getMomentum()[0] if mcp else 0
            mc_py = mcp.getMomentum()[1] if mcp else 0
            mc_pz = mcp.getMomentum()[2] if mcp else 0
            mc_isstopped = int(mcp.isStopped()) if mcp else -1
            if mcp:
                vx, vy, vz = mcp.getVertex()[0], mcp.getVertex()[1], mcp.getVertex()[2]
                ex, ey, ez = mcp.getEndpoint()[0], mcp.getEndpoint()[1], mcp.getEndpoint()[2]
                mc_path_length = np.sqrt((ex - vx)**2 + (ey - vy)**2 + (ez - vz)**2)
                vtx = dd4hep.rec.Vector3D(mcp.getVertex()[0] * MM_TO_CM,
                                          mcp.getVertex()[1] * MM_TO_CM,
                                          mcp.getVertex()[2] * MM_TO_CM)
                end = dd4hep.rec.Vector3D(mcp.getEndpoint()[0] * MM_TO_CM,
                                          mcp.getEndpoint()[1] * MM_TO_CM,
                                          mcp.getEndpoint()[2] * MM_TO_CM)
                mc_vertex_distance = surf.distance(vtx) * CM_TO_UM
                mc_endpoint_distance = surf.distance(end) * CM_TO_UM
            else:
                vx, vy, vz = 0, 0, 0
                ex, ey, ez = 0, 0, 0
                mc_path_length = -1
                mc_vertex_distance = -1
                mc_endpoint_distance = -1

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
                "i_event": i_event,
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
                "origin_x": origin_x,
                "origin_y": origin_y,
                "origin_z": origin_z,
                "normal_x": normal_x,
                "normal_y": normal_y,
                "normal_z": normal_z,
                "i_mcp": i_mcp,
                "mc_pid": mc_pid,
                "mc_e": mc_e,
                "mc_px": mc_px,
                "mc_py": mc_py,
                "mc_pz": mc_pz,
                "mc_vx": vx,
                "mc_vy": vy,
                "mc_vz": vz,
                "mc_ex": ex,
                "mc_ey": ey,
                "mc_ez": ez,
                "mc_path_length": mc_path_length,
                "mc_isstopped": mc_isstopped,
                "mc_vertex_distance": mc_vertex_distance,
                "mc_endpoint_distance": mc_endpoint_distance,
            })


    print(f" Total hits: {total_hits}, inside bounds: {inside}, outside bounds: {outside}")

    # create dataframe
    print("Creating dataframe ...")
    return pd.DataFrame(hits)


def post_process(df):

    # add some columns
    print("Adding columns to dataframe ...")
    df["system"] = np.right_shift(df["cellid0"], 0) & 0b1_1111
    df["side"] = np.right_shift(df["cellid0"], 5) & 0b11
    df["layer"] = np.right_shift(df["cellid0"], 7) & 0b11_1111
    df["module"] = np.right_shift(df["cellid0"], 13) & 0b111_1111_1111
    df["sensor"] = np.right_shift(df["cellid0"], 24) & 0b1111_1111
    df["mc_pt"] = np.sqrt(df["mc_px"]**2 + df["mc_py"]**2)

    # sort dataframe
    print("Sorting dataframe ...")
    df = df.sort_values(by=["i_event", "layer", "module", "sensor"])

    # a few numbers
    sensor_edge = 48 # um
    perp_path = 0.1 # mm
    n_inside = (df["inside_bounds"] == True).sum()
    n_outside = (df["inside_bounds"] == False).sum()
    n_inside_short = ((df["inside_bounds"] == True) & (df["path_length"] < EPSILON)).sum()
    n_outside_short = ((df["inside_bounds"] == False) & (df["path_length"] < EPSILON)).sum()
    n_inside_edge = ((df["inside_bounds"] == True) & (df["abs_distance"] > sensor_edge)).sum()
    n_inside_bulk = ((df["inside_bounds"] == True) & (df["abs_distance"] <= sensor_edge)).sum()
    n_outside_edge = ((df["inside_bounds"] == False) & (df["abs_distance"] > sensor_edge)).sum()
    n_outside_bulk = ((df["inside_bounds"] == False) & (df["abs_distance"] <= sensor_edge)).sum()
    n_inside_long = ((df["inside_bounds"] == True) & (df["path_length"] > perp_path)).sum()
    n_outside_long = ((df["inside_bounds"] == False) & (df["path_length"] > perp_path)).sum()
    n_inside_medium = ((df["inside_bounds"] == True) & (df["path_length"].between(EPSILON, perp_path))).sum()
    n_outside_medium = ((df["inside_bounds"] == False) & (df["path_length"].between(EPSILON, perp_path))).sum()
    print(f"Number of hits inside bounds: {n_inside}, outside bounds: {n_outside}")
    print(f"Number of hits with path length < {EPSILON}mm: inside bounds: {n_inside_short}, outside bounds: {n_outside_short}")
    print(f"Number of hits with abs(distance) > {sensor_edge}um: inside bounds: {n_inside_edge}, outside bounds: {n_outside_edge}")
    print(f"Number of hits with abs(distance) <= {sensor_edge}um: inside bounds: {n_inside_bulk}, outside bounds: {n_outside_bulk}")
    print(f"Number of hits with path length > {perp_path}mm: inside bounds: {n_inside_long}, outside bounds: {n_outside_long}")
    print(f"Number of hits with path length between {EPSILON}mm and {perp_path}mm: inside bounds: {n_inside_medium}, outside bounds: {n_outside_medium}")

    # show the dataframe
    # with pd.option_context("display.min_rows", 50,
    #                        "display.max_rows", 50,
    #                       ):
    #     print(df)
    return df


def plot(df):

    # show some stats
    inside = df[df["inside_bounds"] == True]
    outside = df[df["inside_bounds"] == False]
    print(f"Inside bounds:")
    print(inside["abs_distance"].describe())
    print(f"Outside bounds:")
    print(outside["abs_distance"].describe())

    with PdfPages("test_pylcio_surfaces.pdf") as pdf:

        # mc_isstopped
        print("Plotting mc_isstopped to surface ...")
        bins = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
        fig, ax = plt.subplots()
        ax.hist(inside["mc_isstopped"], bins=bins, alpha=0.5, label="Inside bounds")
        ax.hist(outside["mc_isstopped"], bins=bins, alpha=0.5, label="Outside bounds")
        ax.set_xlabel("MC is stopped")
        ax.set_ylabel("Counts")
        ax.set_title("MC is stopped of hits in InnerTrackerBarrel")
        ax.legend()
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()

        # mc_path_length
        print("Plotting mc_path_length to surface ...")
        for bins in [
            np.linspace(-2, 10, 241),
            np.linspace(0, 100, 241),
            np.linspace(0, 1000, 241),
        ]:
            fig, ax = plt.subplots()
            ax.hist(inside["mc_path_length"], bins=bins, alpha=0.5, label="Inside bounds")
            ax.hist(outside["mc_path_length"], bins=bins, alpha=0.5, label="Outside bounds")
            ax.set_xlabel("MC pathlength [mm]")
            ax.set_ylabel("Counts")
            ax.set_title("MC pathlength of hits in InnerTrackerBarrel")
            ax.legend()
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            ax.semilogy()
            pdf.savefig()
            plt.close()

        # mc vertex distance
        print("Plotting mc_vertex_distance to surface ...")
        for bins in [
            np.linspace(-1000, 1000, 101),
        ]:
            fig, ax = plt.subplots()
            ax.hist(inside["mc_vertex_distance"], bins=bins, alpha=0.5, label="Inside bounds")
            ax.hist(outside["mc_vertex_distance"], bins=bins, alpha=0.5, label="Outside bounds")
            ax.set_xlabel("MC vertex distance [mm]")
            ax.set_ylabel("Counts")
            ax.set_title("MC vertex distance of hits in InnerTrackerBarrel")
            ax.legend()
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            ax.semilogy()
            pdf.savefig()
            plt.close()

        # mc endpoint distance
        print("Plotting mc_endpoint_distance to surface ...")
        for bins in [
            np.linspace(-1000, 1000, 101),
        ]:
            fig, ax = plt.subplots()
            ax.hist(inside["mc_endpoint_distance"], bins=bins, alpha=0.5, label="Inside bounds")
            ax.hist(outside["mc_endpoint_distance"], bins=bins, alpha=0.5, label="Outside bounds")
            ax.set_xlabel("MC endpoint distance [mm]")
            ax.set_ylabel("Counts")
            ax.set_title("MC endpoint distance of hits in InnerTrackerBarrel")
            ax.legend()
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            ax.semilogy()
            pdf.savefig()
            plt.close()

        # energy
        print("Plotting energy to surface ...")
        for bins in [
            np.linspace(0, 10, 201),
            np.linspace(0, 100, 201),
            np.linspace(0, 1000, 201),
        ]:
            fig, ax = plt.subplots()
            ax.hist(inside["energy"], bins=bins, alpha=0.5, label="Inside bounds")
            ax.hist(outside["energy"], bins=bins, alpha=0.5, label="Outside bounds")
            ax.set_xlabel("Energy [keV]")
            ax.set_ylabel("Counts")
            ax.set_title("Energy of hits in InnerTrackerBarrel")
            ax.legend()
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            ax.semilogy()
            pdf.savefig()
            plt.close()

        # distance
        print("Plotting distance to surface ...")
        fig, ax = plt.subplots()
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
        fig, ax = plt.subplots()
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
            np.linspace(0, 0.1, 501),
            np.linspace(0, 1, 501),
            np.linspace(0, 10, 201),
        ]:
            fig, ax = plt.subplots()
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

        # plots when path length less than 1e-3mm
        cut = EPSILON
        inside_cut = inside[inside["path_length"] < cut]
        outside_cut = outside[outside["path_length"] < cut]
        n_inside_cut = len(inside_cut)
        n_outside_cut = len(outside_cut)

        # distance when short path length
        print("Plotting distance to surface when path length < 1e-3mm ...")
        fig, ax = plt.subplots()
        bins = np.linspace(-60, 60, 121)
        ax.hist(inside_cut["distance"], bins=bins, alpha=0.5, label=f"Inside bounds, n={n_inside_cut}")
        ax.hist(outside_cut["distance"], bins=bins, alpha=0.5, label=f"Outside bounds, n={n_outside_cut}")
        ax.set_xlabel("Distance to surface [um]")
        ax.set_ylabel("Counts") 
        ax.set_title(f"Distance to surface when path length < {cut}mm in InnerTrackerBarrel")
        ax.legend()
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()

        # energy when short path length
        print("Plotting energy to surface when path length < 1e-3 mm ...")
        fig, ax = plt.subplots()
        bins = np.linspace(0, 10, 201)
        ax.hist(inside_cut["energy"], bins=bins, alpha=0.5, label=f"Inside bounds, n={n_inside_cut}")
        ax.hist(outside_cut["energy"], bins=bins, alpha=0.5, label=f"Outside bounds, n={n_outside_cut}")
        ax.set_xlabel("Energy [keV]")
        ax.set_ylabel("Counts")
        ax.set_title(f"Energy when path length < {cut}mm in InnerTrackerBarrel")
        ax.legend()
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        ax.semilogy()
        pdf.savefig()
        plt.close()
        return

        # distance vs cos theta
        print("Plotting distance vs incidence angle ...")
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            for norm in [None, colors.LogNorm()]:
                fig, ax = plt.subplots()
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


        # distance vs path length
        print("Plotting distance vs path length ...")
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            for norm in [None, colors.LogNorm()]:
                fig, ax = plt.subplots()
                bins = [np.linspace(0, 1, 201),
                        np.linspace(-60, 60, 121),
                        ]
                # log-z scale
                _, _, _, im = ax.hist2d(
                        the_df["path_length"],
                        the_df["distance"],
                        bins=bins,
                        cmap="hot",
                        cmin=0.5,
                        norm=norm,
                        )
                fig.colorbar(im, ax=ax, pad=0.01, label="Counts")
                ax.set_xlabel("Path length [mm]")
                ax.set_ylabel("Distance to surface [um]")
                ax.set_title(f"Distance vs path length {tag} bounds")
                fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                pdf.savefig()
                plt.close()


        # path length vs cos theta
        print("Plotting path length vs incidence angle ...")
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            for norm in [None, colors.LogNorm()]:
                fig, ax = plt.subplots()
                bins = 100
                bins = [
                    np.linspace(0, 1, 501),
                    np.linspace(-1, 1, 201),
                ]
                _, _, _, im = ax.hist2d(
                    the_df["path_length"],
                    the_df["cos_theta"],
                    bins=bins,
                    cmap="hot",
                    cmin=0.5,
                    norm=norm,
                )
                ax.set_xlabel("Path length [mm]")
                ax.set_ylabel("Cosine of incidence angle")
                ax.set_title(f"{tag} bounds")
                fig.colorbar(im, ax=ax, pad=0.01, label="Counts")
                fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
                pdf.savefig()
                plt.close()

        # local u vs v
        print("Plotting local u vs v ...")
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            fig, ax = plt.subplots()
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
                fig, ax = plt.subplots()
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

        # local u vs v when path length < 0.05 and abs(cos theta) > 0.75
        print("Plotting local u vs v with different path length and incidence angles ...")
        cut_path_length = 50 # um
        cut_cos_theta = 0.75
        bins = [
            np.linspace(-24, 24, 241),
            np.linspace(-24, 24, 241),
        ]
        for the_df, tag in [(inside, "inside"),
                            (outside, "outside"),
                           ]:
            scenario = f"path_length < {cut_path_length}um, abs(cos(theta)) > {cut_cos_theta}"
            mask = (
                ((the_df["path_length"] * MM_TO_UM) < cut_path_length) &
                (abs(the_df["cos_theta"]) > cut_cos_theta)
            )
            sel = the_df[mask]
            fig, ax = plt.subplots()
            _, _, _, im = ax.hist2d(
                sel["local_u"],
                sel["local_v"],
                bins=bins,
                cmap="hot",
                cmin=0.5,
            )
            ax.set_xlabel("Local u [mm]")
            ax.set_ylabel("Local v [mm]")
            ax.set_title(f"Hits {tag}, {scenario}")
            fig.colorbar(im, ax=ax, pad=0.01, label="Counts")
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            plt.close()


if __name__ == "__main__":
    main()


