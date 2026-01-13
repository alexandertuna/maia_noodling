import os
import numpy as np
import pandas as pd
import multiprocessing as mp

from constants import OUTSIDE_BOUNDS, INSIDE_BOUNDS, UNDEFINED_BOUNDS

_detector = None
_surfman = None
_maps = None

EPSILON = 1e-6
MCPARTICLE = "MCParticle"
MUON = 13
SPEED_OF_LIGHT = 299.792458  # mm/ns
COLLECTIONS = [
    # "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
PARTICLES_OF_INTEREST = [MUON]

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
    simhits = []

    # loop over all events in the slcio file
    for i_event, event in enumerate(reader):

        # inspect tracking detectors
        for collection in COLLECTIONS:

            col = event.getCollection(collection)
            n_hit = len(col)

            for i_hit, hit in enumerate(col):

                if i_hit % 1000000 == 0:
                    print(f"Processing file {os.path.basename(slcio_file_path)} "
                          f"event {i_event} collection {collection} "
                          f"hit {i_hit}/{n_hit} ...")
                if not hit:
                    continue
                # ONLY OT LAYERS 0 AND 1 FOR NOW
                if (np.right_shift(hit.getCellID0(), 7) & 0b11_1111) not in [0, 1]:
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
                simhits.append({
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
                })

    # Close the 
    reader.close()

    # Convert the list of hits to a pandas DataFrame and postprocess
    print("Creating DataFrame ...")
    df = pd.DataFrame(simhits)
    return postprocess_dataframe(df)


def postprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    print("Postprocessing DataFrame ...")
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
    df["simhit_layer_mod_2"] = df["simhit_layer"] % 2

    # remove redundant columns
    df.drop(columns=[
        # "simhit_x",
        # "simhit_y",
        "simhit_R",
        "simhit_theta",
        # "simhit_cellid0",
    ], inplace=True)

    # sort columns alphabetically
    return df[sorted(df.columns)]


def sort_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    print("Sorting DataFrame ...")
    columns = [
        "file",
        "i_event",
        "simhit_system",
        "simhit_layer",
        "simhit_module",
        "simhit_sensor",
    ]
    return df.sort_values(by=columns).reset_index(drop=True)

