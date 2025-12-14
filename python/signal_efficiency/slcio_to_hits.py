try:
    import pyLCIO
    import dd4hep
    import DDRec
except ImportError as e:
    print("pyLCIO is not installed. Will continue onward and see what happens ...")

import os
import numpy as np
import pandas as pd
import multiprocessing as mp

MCPARTICLE = "MCParticle"
MUON = 13
SPEED_OF_LIGHT = 299.792458  # mm/ns
ONE_MM = 1.0
ONE_GEV = 1.0
HALF_SENSOR_THICKNESS = 50.0 # um
EPSILON = 1e-6
EPSILON_INSIDE_BOUNDS = 1.0
BARREL_TRACKER_MAX_RADIUS = 1446.0
BARREL_TRACKER_MAX_Z = 1264.2
BARREL_TRACKER_MAX_THETA = np.arctan(BARREL_TRACKER_MAX_RADIUS / BARREL_TRACKER_MAX_Z)
BARREL_TRACKER_MAX_ETA = -np.log(np.tan(BARREL_TRACKER_MAX_THETA / 2.0))
print("BARREL_TRACKER_MAX_ETA", BARREL_TRACKER_MAX_ETA)

MM_TO_CM = 0.1
CM_TO_MM = 10.0

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"


class SlcioToHitsDataFrame:

    def __init__(
            self,
            slcio_file_paths,
            collections,
        ):
        self.slcio_file_paths = slcio_file_paths
        self.collections = collections
        self.load_geometry = True


    def convert(self) -> pd.DataFrame:
        df = self.convert_all_files()
        df = self.postprocess_dataframe(df)
        df = self.filter_dataframe(df)
        df = self.sort_dataframe(df)
        return df


    def convert_all_files(self) -> pd.DataFrame:
        print(f"Converting {len(self.slcio_file_paths)} slcio files to a DataFrame ...")
        with mp.Pool() as pool:
            all_hits_dfs = pool.map(self.convert_one_file, self.slcio_file_paths)
        print("Merging DataFrames ...")
        return pd.concat(all_hits_dfs, ignore_index=True)


    def convert_one_file(self, slcio_file_path: str) -> pd.DataFrame:
        # print(f"Converting slcio file to DataFrame: {slcio_file_path}")

        # setup the detector
        if self.load_geometry:
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

        # open the SLCIO file
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(slcio_file_path)

        # list for holding all hits
        rows = []

        # loop over all events in the slcio file
        for i_event, event in enumerate(reader):

            # inspect mcparticles
            mcparticles = list(event.getCollection(MCPARTICLE))
            sim_px = [mcp.getMomentum()[0] for mcp in mcparticles]
            sim_py = [mcp.getMomentum()[1] for mcp in mcparticles]
            sim_pz = [mcp.getMomentum()[2] for mcp in mcparticles]
            sim_m = [mcp.getMass() for mcp in mcparticles]
            sim_q = [mcp.getCharge() for mcp in mcparticles]
            sim_pdg = [mcp.getPDG() for mcp in mcparticles]
            sim_vertex_x = [mcp.getVertex()[0] for mcp in mcparticles]
            sim_vertex_y = [mcp.getVertex()[1] for mcp in mcparticles]
            sim_vertex_z = [mcp.getVertex()[2] for mcp in mcparticles]
            sim_endpoint_x = [mcp.getEndpoint()[0] for mcp in mcparticles]
            sim_endpoint_y = [mcp.getEndpoint()[1] for mcp in mcparticles]
            sim_endpoint_z = [mcp.getEndpoint()[2] for mcp in mcparticles]
            for i_sim in range(len(mcparticles)):
                if abs(sim_pdg[i_sim]) != MUON:
                    continue
                rows.append({
                    'hit': False,
                    'file': os.path.basename(slcio_file_path),
                    'i_event': i_event,
                    'hit_x': 0,
                    'hit_y': 0,
                    'hit_z': 0,
                    'hit_e': 0,
                    'hit_t': 0,
                    'hit_cellid0': 0,
                    'hit_pathlength': 0,
                    'hit_inside_bounds': False,
                    'hit_distance': 0,
                    'i_sim': i_sim,
                    'sim_px': sim_px[i_sim],
                    'sim_py': sim_py[i_sim],
                    'sim_pz': sim_pz[i_sim],
                    'sim_m': sim_m[i_sim],
                    'sim_q': sim_q[i_sim],
                    'sim_pdg': sim_pdg[i_sim],
                    'sim_vertex_x': sim_vertex_x[i_sim],
                    'sim_vertex_y': sim_vertex_y[i_sim],
                    'sim_vertex_z': sim_vertex_z[i_sim],
                    'sim_endpoint_x': sim_endpoint_x[i_sim],
                    'sim_endpoint_y': sim_endpoint_y[i_sim],
                    'sim_endpoint_z': sim_endpoint_z[i_sim],
                })

            # inspect tracking detector collections
            for collection in self.collections:

                col = event.getCollection(collection)

                for hit in col:

                    mcp = hit.getMCParticle()

                    # skip if hit or mcp is missing
                    if not hit:
                        continue
                    if not mcp:
                        continue
                    if not mcp in mcparticles:
                        continue
                    i_sim = mcparticles.index(mcp)

                    # # ------------------------------------------------------------
                    # # try putting cuts here
                    # """
                    # (df["sim_q"] != 0) &
                    # (df["sim_vertex_r"] < ONE_MM) &
                    # (df["sim_vertex_z"] < ONE_MM) &
                    # (df["sim_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
                    # (np.abs(df["sim_eta"]) < BARREL_TRACKER_MAX_ETA)
                    # """
                    # if abs(sim_pdg[i_sim]) != MUON:
                    #     continue
                    # sim_vertex_r = np.sqrt(sim_vertex_x[i_sim]**2 + sim_vertex_y[i_sim]**2)
                    # if sim_vertex_r >= ONE_MM:
                    #     continue
                    # if abs(sim_vertex_z[i_sim]) >= ONE_MM:
                    #     continue
                    # sim_endpoint_r = np.sqrt(sim_endpoint_x[i_sim]**2 + sim_endpoint_y[i_sim]**2)
                    # if sim_endpoint_r <= BARREL_TRACKER_MAX_RADIUS:
                    #     continue
                    # sim_theta = np.arctan2(
                    #     np.sqrt(sim_px[i_sim]**2 + sim_py[i_sim]**2),
                    #     sim_pz[i_sim],
                    # )
                    # sim_eta = -np.log(np.tan(sim_theta / 2.0))
                    # if abs(sim_eta) >= BARREL_TRACKER_MAX_ETA:
                    #     continue
                    # # ------------------------------------------------------------

                    # hit/surface relations
                    if self.load_geometry:
                        surf = maps[collection].find(hit.getCellID0()).second
                        pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                                hit.getPosition()[1] * MM_TO_CM,
                                                hit.getPosition()[2] * MM_TO_CM)
                        inside_bounds = surf.insideBounds(pos) # EPSILON_INSIDE_BOUNDS
                        distance = surf.distance(pos) * CM_TO_MM
                    else:
                        inside_bounds = True
                        distance = -1

                    # record the hit info
                    rows.append({
                        'hit': True,
                        'file': os.path.basename(slcio_file_path),
                        'i_event': i_event,
                        'hit_x': hit.getPosition()[0],
                        'hit_y': hit.getPosition()[1],
                        'hit_z': hit.getPosition()[2],
                        'hit_e': hit.getEDep(),
                        'hit_t': hit.getTime(),
                        'hit_cellid0': hit.getCellID0(),
                        'hit_pathlength': hit.getPathLength(),
                        'hit_inside_bounds': inside_bounds,
                        'hit_distance': distance,
                        'i_sim': i_sim,
                        'sim_px': sim_px[i_sim],
                        'sim_py': sim_py[i_sim],
                        'sim_pz': sim_pz[i_sim],
                        'sim_m': sim_m[i_sim],
                        'sim_q': sim_q[i_sim],
                        'sim_pdg': sim_pdg[i_sim],
                        'sim_vertex_x': sim_vertex_x[i_sim],
                        'sim_vertex_y': sim_vertex_y[i_sim],
                        'sim_vertex_z': sim_vertex_z[i_sim],
                        'sim_endpoint_x': sim_endpoint_x[i_sim],
                        'sim_endpoint_y': sim_endpoint_y[i_sim],
                        'sim_endpoint_z': sim_endpoint_z[i_sim],
                    })

        # Close the reader
        reader.close()

        # Convert the list of hits to a pandas DataFrame
        return pd.DataFrame(rows)


    def postprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Postprocessing DataFrame ...")
        df["sim_pt"] = np.sqrt(df["sim_px"]**2 + df["sim_py"]**2)
        df["sim_theta"] = np.arctan2(df["sim_pt"], df["sim_pz"])
        df["sim_eta"] = -np.log(np.tan(df["sim_theta"] / 2))
        df["sim_phi"] = np.arctan2(df["sim_py"], df["sim_px"])
        df["sim_vertex_r"] = np.sqrt(df["sim_vertex_x"]**2 + df["sim_vertex_y"]**2)
        df["sim_endpoint_r"] = np.sqrt(df["sim_endpoint_x"]**2 + df["sim_endpoint_y"]**2)
        df["hit_r"] = np.sqrt(df["hit_x"]**2 + df["hit_y"]**2)
        df["hit_R"] = np.sqrt(df["hit_x"]**2 + df["hit_y"]**2 + df["hit_z"]**2)
        df["hit_t_corrected"] = df["hit_t"] - (df["hit_R"] / SPEED_OF_LIGHT)
        df["hit_system"] = np.right_shift(df["hit_cellid0"], 0) & 0b1_1111
        df["hit_side"] = np.right_shift(df["hit_cellid0"], 5) & 0b11
        df["hit_layer"] = np.right_shift(df["hit_cellid0"], 7) & 0b11_1111
        df["hit_module"] = np.right_shift(df["hit_cellid0"], 13) & 0b111_1111_1111
        df["hit_sensor"] = np.right_shift(df["hit_cellid0"], 24) & 0b1111_1111
        df["hit_phi"] = np.arctan2(df["hit_y"], df["hit_x"])
        df["hit_theta"] = np.maximum(np.arctan2(df["hit_r"], df["hit_z"]), EPSILON)
        df["hit_eta"] = -np.log(np.tan(df["hit_theta"] / 2))

        # remove redundant columns
        df.drop(columns=[
            "sim_px",
            "sim_py",
            "sim_theta",
            "sim_vertex_x",
            "sim_vertex_y",
            "sim_endpoint_x",
            "sim_endpoint_y",
            "hit_x",
            "hit_y",
            "hit_R",
            "hit_theta",
            "hit_cellid0",
        ], inplace=True)

        # sort columns alphabetically
        return df[sorted(df.columns)]


    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = (
            (df["sim_q"] != 0) &
            (df["sim_pt"] > ONE_GEV) &
            (df["sim_vertex_r"] < ONE_MM) &
            (np.abs(df["sim_vertex_z"]) < ONE_MM) &
            (df["sim_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
            (np.abs(df["sim_eta"]) < BARREL_TRACKER_MAX_ETA) &
            (df["hit_inside_bounds"] | (~df["hit"]))
        )
            # (np.abs(df["hit_distance"]) < HALF_SENSOR_THICKNESS)
        n_pass, n_total = mask.sum(), len(mask)
        print(f"Keeping {n_pass} / {n_total} rows when filtering ...")
        return df[mask].reset_index(drop=True)


    def sort_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Sorting DataFrame ...")
        columns = [
            "file",
            "i_event",
            "i_sim",
            "hit",
            "hit_system",
            "hit_layer",
        ]
        return df.sort_values(by=columns).reset_index(drop=True)

