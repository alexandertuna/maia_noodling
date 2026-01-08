import os
import numpy as np
import pandas as pd
import multiprocessing as mp

from constants import BARREL_TRACKER_MAX_ETA
from constants import BARREL_TRACKER_MAX_RADIUS
from constants import ONE_GEV, ONE_MM
from constants import OUTSIDE_BOUNDS, INSIDE_BOUNDS, UNDEFINED_BOUNDS

_detector = None
_surfman = None
_maps = None

MCPARTICLE = "MCParticle"
MUON = 13
SPEED_OF_LIGHT = 299.792458  # mm/ns
HALF_SENSOR_THICKNESS = 50.0 # um
EPSILON = 1e-6
EPSILON_INSIDE_BOUNDS = 1.0
COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
PARTICLES_OF_INTEREST = [MUON]
print("BARREL_TRACKER_MAX_ETA", BARREL_TRACKER_MAX_ETA)

MM_TO_CM = 0.1
CM_TO_MM = 10.0

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"


class SlcioToHitsDataFrame:

    def __init__(
            self,
            slcio_file_paths: list[str],
            load_geometry: bool,
        ):
        self.slcio_file_paths = slcio_file_paths
        self.load_geometry = load_geometry


    def convert(self) -> pd.DataFrame:
        df = self.convert_all_files()
        df = filter_dataframe(df)
        df = sort_dataframe(df)
        return df


    def convert_all_files(self) -> pd.DataFrame:
        print(f"Converting {len(self.slcio_file_paths)} slcio files to a DataFrame ...")
        init_function = init_worker if self.load_geometry else init_dummy
        with mp.Pool(initializer=init_function) as pool:
            n_map = len(self.slcio_file_paths)
            load_geometry = [self.load_geometry]*n_map
            all_hits_dfs = pool.starmap(
                convert_one_file,
                zip(self.slcio_file_paths,
                    load_geometry,
                )
            )
        print("Merging DataFrames ...")
        return pd.concat(all_hits_dfs, ignore_index=True)


def init_dummy():
    pass


def init_worker():
    global _detector, _surfman, _maps
    import dd4hep, DDRec
    _detector = dd4hep.Detector.getInstance()
    _detector.fromCompact(XML)
    _surfman = DDRec.SurfaceManager(_detector)
    dets = {
        "InnerTrackerBarrelCollection": _detector.detector("InnerTrackerBarrel"),
        "OuterTrackerBarrelCollection": _detector.detector("OuterTrackerBarrel"),
    }
    _maps = {name: _surfman.map(det.name()) for name, det in dets.items()}


def convert_one_file(
        slcio_file_path: str,
        load_geometry: bool,
    ) -> pd.DataFrame:

    # import here to avoid:
    #  - unnecessary imports if not used
    #  - issues with multiprocessing
    import pyLCIO
    if load_geometry:
        import dd4hep
        import DDRec

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
            # big speedup by skipping unwanted particles early
            if abs(mcp_pdg[i_mcp]) not in PARTICLES_OF_INTEREST:
                continue
            rows.append({
                'simhit': False,
                'file': os.path.basename(slcio_file_path),
                'i_event': i_event,
                'simhit_x': 0,
                'simhit_y': 0,
                'simhit_z': 0,
                'simhit_e': 0,
                'simhit_t': 0,
                'simhit_cellid0': 0,
                'simhit_pathlength': 0,
                'simhit_inside_bounds': UNDEFINED_BOUNDS,
                'simhit_distance': 0,
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

        # inspect tracking detectors
        for collection in COLLECTIONS:

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
                if abs(mcp_pdg[i_mcp]) not in PARTICLES_OF_INTEREST:
                    continue

                # hit/surface relations
                if load_geometry:
                    surf = _maps[collection].find(hit.getCellID0()).second
                    pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                              hit.getPosition()[1] * MM_TO_CM,
                                              hit.getPosition()[2] * MM_TO_CM)
                    inside_bounds = INSIDE_BOUNDS if surf.insideBounds(pos) else OUTSIDE_BOUNDS
                    distance = surf.distance(pos) * CM_TO_MM
                else:
                    inside_bounds = UNDEFINED_BOUNDS
                    distance = -1

                # record the hit info
                rows.append({
                    'simhit': True,
                    'file': os.path.basename(slcio_file_path),
                    'i_event': i_event,
                    'simhit_x': hit.getPosition()[0],
                    'simhit_y': hit.getPosition()[1],
                    'simhit_z': hit.getPosition()[2],
                    'simhit_px': hit.getMomentum()[0],
                    'simhit_py': hit.getMomentum()[1],
                    'simhit_pz': hit.getMomentum()[2],
                    'simhit_e': hit.getEDep(),
                    'simhit_t': hit.getTime(),
                    'simhit_cellid0': hit.getCellID0(),
                    'simhit_pathlength': hit.getPathLength(),
                    'simhit_inside_bounds': inside_bounds,
                    'simhit_distance': distance,
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

    # Convert the list of hits to a pandas DataFrame and postprocess
    df = pd.DataFrame(rows)
    return postprocess_dataframe(df)


def postprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # print("Postprocessing DataFrame ...")
    df["mcp_p"] = np.sqrt(df["mcp_px"]**2 + df["mcp_py"]**2 + df["mcp_pz"]**2)
    df["mcp_pt"] = np.sqrt(df["mcp_px"]**2 + df["mcp_py"]**2)
    df["mcp_theta"] = np.arctan2(df["mcp_pt"], df["mcp_pz"])
    df["mcp_eta"] = -np.log(np.tan(df["mcp_theta"] / 2))
    df["mcp_phi"] = np.arctan2(df["mcp_py"], df["mcp_px"])
    df["mcp_q_over_pt"] = df["mcp_q"] / df["mcp_pt"]
    df["mcp_vertex_r"] = np.sqrt(df["mcp_vertex_x"]**2 + df["mcp_vertex_y"]**2)
    df["mcp_endpoint_r"] = np.sqrt(df["mcp_endpoint_x"]**2 + df["mcp_endpoint_y"]**2)
    df["simhit_r"] = np.sqrt(df["simhit_x"]**2 + df["simhit_y"]**2)
    df["simhit_R"] = np.sqrt(df["simhit_x"]**2 + df["simhit_y"]**2 + df["simhit_z"]**2)
    df["simhit_t_corrected"] = df["simhit_t"] - (df["simhit_R"] / SPEED_OF_LIGHT)
    df["simhit_system"] = np.right_shift(df["simhit_cellid0"], 0) & 0b1_1111
    df["simhit_side"] = np.right_shift(df["simhit_cellid0"], 5) & 0b11
    df["simhit_layer"] = np.right_shift(df["simhit_cellid0"], 7) & 0b11_1111
    df["simhit_module"] = np.right_shift(df["simhit_cellid0"], 13) & 0b111_1111_1111
    df["simhit_sensor"] = np.right_shift(df["simhit_cellid0"], 24) & 0b1111_1111
    df["simhit_phi"] = np.arctan2(df["simhit_y"], df["simhit_x"])
    df["simhit_theta"] = np.maximum(np.arctan2(df["simhit_r"], df["simhit_z"]), EPSILON)
    df["simhit_eta"] = -np.log(np.tan(df["simhit_theta"] / 2))
    df["simhit_pt"] = np.sqrt(df["simhit_px"]**2 + df["simhit_py"]**2)
    df["simhit_p"] = np.sqrt(df["simhit_px"]**2 + df["simhit_py"]**2 + df["simhit_pz"]**2)
    df["simhit_costheta"] = (df["simhit_x"] * df["simhit_px"] + df["simhit_y"] * df["simhit_py"] + df["simhit_z"] * df["simhit_pz"]) / (df["simhit_R"] * df["simhit_p"])
    df["simhit_layer_div_2"] = df["simhit_layer"] // 2

    # remove redundant columns
    df.drop(columns=[
        "mcp_px",
        "mcp_py",
        "mcp_theta",
        "mcp_vertex_x",
        "mcp_vertex_y",
        "mcp_endpoint_x",
        "mcp_endpoint_y",
        "simhit_x",
        "simhit_y",
        "simhit_R",
        "simhit_theta",
        # "simhit_cellid0",
    ], inplace=True)

    # sort columns alphabetically
    return df[sorted(df.columns)]


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    mask = (
        (abs(df["mcp_pdg"]).isin(PARTICLES_OF_INTEREST)) &
        (df["mcp_q"] != 0) &
        (df["mcp_pt"] > ONE_GEV) &
        (df["mcp_vertex_r"] < ONE_MM) &
        (np.abs(df["mcp_vertex_z"]) < ONE_MM) &
        (df["mcp_endpoint_r"] > BARREL_TRACKER_MAX_RADIUS) &
        (np.abs(df["mcp_eta"]) < BARREL_TRACKER_MAX_ETA)
    )
    n_pass, n_total = mask.sum(), len(mask)
    print(f"Keeping {n_pass} / {n_total} rows when filtering")
    return df[mask].reset_index(drop=True)


def sort_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    print("Sorting DataFrame ...")
    columns = [
        "file",
        "i_event",
        "i_mcp",
        "simhit",
        "simhit_system",
        "simhit_layer",
    ]
    return df.sort_values(by=columns).reset_index(drop=True)

