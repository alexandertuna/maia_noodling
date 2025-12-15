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
            mcp_px = [mcp.getMomentum()[0] for mcp in mcparticles]
            mcp_py = [mcp.getMomentum()[1] for mcp in mcparticles]
            mcp_pz = [mcp.getMomentum()[2] for mcp in mcparticles]
            mcp_m = [mcp.getMass() for mcp in mcparticles]
            mcp_q = [mcp.getCharge() for mcp in mcparticles]
            mcp_pdg = [mcp.getPDG() for mcp in mcparticles]
            mcp_vertex_x = [mcp.getVertex()[0] for mcp in mcparticles]
            mcp_vertex_y = [mcp.getVertex()[1] for mcp in mcparticles]
            mcp_vertex_z = [mcp.getVertex()[2] for mcp in mcparticles]
            mcp_endpoint_x = [mcp.getEndpoint()[0] for mcp in mcparticles]
            mcp_endpoint_y = [mcp.getEndpoint()[1] for mcp in mcparticles]
            mcp_endpoint_z = [mcp.getEndpoint()[2] for mcp in mcparticles]
            for i_mcp in range(len(mcparticles)):
                if abs(mcp_pdg[i_mcp]) != MUON:
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
                    'i_mcp': i_mcp,
                    'mcp_px': mcp_px[i_mcp],
                    'mcp_py': mcp_py[i_mcp],
                    'mcp_pz': mcp_pz[i_mcp],
                    'mcp_m': mcp_m[i_mcp],
                    'mcp_q': mcp_q[i_mcp],
                    'mcp_pdg': mcp_pdg[i_mcp],
                    'mcp_vertex_x': mcp_vertex_x[i_mcp],
                    'mcp_vertex_y': mcp_vertex_y[i_mcp],
                    'mcp_vertex_z': mcp_vertex_z[i_mcp],
                    'mcp_endpoint_x': mcp_endpoint_x[i_mcp],
                    'mcp_endpoint_y': mcp_endpoint_y[i_mcp],
                    'mcp_endpoint_z': mcp_endpoint_z[i_mcp],
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
                    i_mcp = mcparticles.index(mcp)

                    # # ------------------------------------------------------------
                    # # try putting cuts here
                    # """
                    # (df["mcp_q"] != 0) &
                    # (df["mcp_vertex_r"] < ONE_MM) &
                    # (df["mcp_vertex_z"] < ONE_MM) &
                    # (df["mcp_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
                    # (np.abs(df["mcp_eta"]) < BARREL_TRACKER_MAX_ETA)
                    # """
                    # if abs(mcp_pdg[i_mcp]) != MUON:
                    #     continue
                    # mcp_vertex_r = np.sqrt(mcp_vertex_x[i_mcp]**2 + mcp_vertex_y[i_mcp]**2)
                    # if mcp_vertex_r >= ONE_MM:
                    #     continue
                    # if abs(mcp_vertex_z[i_mcp]) >= ONE_MM:
                    #     continue
                    # mcp_endpoint_r = np.sqrt(mcp_endpoint_x[i_mcp]**2 + mcp_endpoint_y[i_mcp]**2)
                    # if mcp_endpoint_r <= BARREL_TRACKER_MAX_RADIUS:
                    #     continue
                    # mcp_theta = np.arctan2(
                    #     np.sqrt(mcp_px[i_mcp]**2 + mcp_py[i_mcp]**2),
                    #     mcp_pz[i_mcp],
                    # )
                    # mcp_eta = -np.log(np.tan(mcp_theta / 2.0))
                    # if abs(mcp_eta) >= BARREL_TRACKER_MAX_ETA:
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
                        'i_mcp': i_mcp,
                        'mcp_px': mcp_px[i_mcp],
                        'mcp_py': mcp_py[i_mcp],
                        'mcp_pz': mcp_pz[i_mcp],
                        'mcp_m': mcp_m[i_mcp],
                        'mcp_q': mcp_q[i_mcp],
                        'mcp_pdg': mcp_pdg[i_mcp],
                        'mcp_vertex_x': mcp_vertex_x[i_mcp],
                        'mcp_vertex_y': mcp_vertex_y[i_mcp],
                        'mcp_vertex_z': mcp_vertex_z[i_mcp],
                        'mcp_endpoint_x': mcp_endpoint_x[i_mcp],
                        'mcp_endpoint_y': mcp_endpoint_y[i_mcp],
                        'mcp_endpoint_z': mcp_endpoint_z[i_mcp],
                    })

        # Close the reader
        reader.close()

        # Convert the list of hits to a pandas DataFrame
        return pd.DataFrame(rows)


    def postprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Postprocessing DataFrame ...")
        df["mcp_pt"] = np.sqrt(df["mcp_px"]**2 + df["mcp_py"]**2)
        df["mcp_theta"] = np.arctan2(df["mcp_pt"], df["mcp_pz"])
        df["mcp_eta"] = -np.log(np.tan(df["mcp_theta"] / 2))
        df["mcp_phi"] = np.arctan2(df["mcp_py"], df["mcp_px"])
        df["mcp_vertex_r"] = np.sqrt(df["mcp_vertex_x"]**2 + df["mcp_vertex_y"]**2)
        df["mcp_endpoint_r"] = np.sqrt(df["mcp_endpoint_x"]**2 + df["mcp_endpoint_y"]**2)
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
            "mcp_px",
            "mcp_py",
            "mcp_theta",
            "mcp_vertex_x",
            "mcp_vertex_y",
            "mcp_endpoint_x",
            "mcp_endpoint_y",
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
            (df["mcp_q"] != 0) &
            (df["mcp_pt"] > ONE_GEV) &
            (df["mcp_vertex_r"] < ONE_MM) &
            (np.abs(df["mcp_vertex_z"]) < ONE_MM) &
            (df["mcp_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
            (np.abs(df["mcp_eta"]) < BARREL_TRACKER_MAX_ETA) &
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
            "i_mcp",
            "hit",
            "hit_system",
            "hit_layer",
        ]
        return df.sort_values(by=columns).reset_index(drop=True)

