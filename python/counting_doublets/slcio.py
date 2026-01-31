import contextlib
import os
import sys
import numpy as np
import pandas as pd
import multiprocessing as mp

from constants import OUTSIDE_BOUNDS, INSIDE_BOUNDS, UNDEFINED_BOUNDS, BOUNDS
from constants import SIGNAL
from constants import EPSILON, MCPARTICLE, PARTICLES_OF_INTEREST, SPEED_OF_LIGHT
from constants import MM_TO_CM, CM_TO_MM
from constants import XML
from constants import COLLECTIONS

_detector = None
_surfman = None
_maps = None

class SlcioToHitsDataFrame:

    def __init__(
            self,
            slcio_file_paths: list[str],
            load_geometry: bool,
        ):
        self.slcio_file_paths = slcio_file_paths
        self.load_geometry = load_geometry


    def convert(self) -> pd.DataFrame:
        mcps, simhits = self.convert_all_files()
        mcps = sort_mcps(mcps)
        simhits = sort_simhits(simhits)
        announce_inside_bounds(simhits)
        return mcps, simhits


    def convert_all_files(self) -> pd.DataFrame:
        print(f"Converting {len(self.slcio_file_paths)} slcio files to a DataFrame ...")
        initializer = init_worker if self.load_geometry else init_dummy
        processes = min(mp.cpu_count(), len(self.slcio_file_paths))
        with mp.Pool(processes=processes, initializer=initializer) as pool:
            n_map = len(self.slcio_file_paths)
            load_geometry = [self.load_geometry]*n_map
            results = pool.starmap(
                convert_one_file,
                zip(self.slcio_file_paths,
                    load_geometry,
                )
            )
        print("Merging DataFrames ...")
        return [
            pd.concat([res[0] for res in results], ignore_index=True),
            pd.concat([res[1] for res in results], ignore_index=True),
        ]


def init_dummy():
    pass


def init_worker():
    # Sorry for these global variables. They are needed for multiprocessing
    global _detector, _surfman, _maps
    import dd4hep, DDRec
    dd4hep.setPrintLevel(dd4hep.PrintLevel.WARNING)
    with silence_c_stdout_stderr():
        # Sorry for this context manager. dd4hep can be very noisy
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

    # check if signal
    signal = SIGNAL in os.path.basename(slcio_file_path)

    # open the SLCIO file
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(slcio_file_path)

    # list for holding all hits
    mcps = []
    simhits = []

    # loop over all events in the slcio file
    for i_event, event in enumerate(reader):

        # inspect MCParticles
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
            if abs(mcp_pdg[i_mcp]) not in PARTICLES_OF_INTEREST:
                continue
            mcps.append({
                'file': os.path.basename(slcio_file_path),
                'i_event': i_event,
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
            n_hit = len(col)

            for i_hit, hit in enumerate(col):

                if i_hit > 0 and i_hit % 1000000 == 0:
                    print(f"Processing file {os.path.basename(slcio_file_path)} "
                          f"event {i_event} collection {collection} "
                          f"hit {i_hit}/{n_hit} ...")
                if not hit:
                    continue
                # ONLY OT LAYERS 0 AND 1 FOR NOW
                if (np.right_shift(hit.getCellID0(), 7) & 0b11_1111) not in [0, 1]:
                    continue

                # associated MCParticle
                mcp = hit.getMCParticle()
                i_mcp = mcparticles.index(mcp) if mcp in mcparticles else -1

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

                # ignore hits outside bounds
                if inside_bounds == OUTSIDE_BOUNDS:
                    continue

                # record the hit info
                simhits.append({
                    'file': os.path.basename(slcio_file_path),
                    'i_event': i_event,
                    'i_mcp': i_mcp,
                    'simhit_signal': signal,
                    'simhit_x': hit.getPosition()[0],
                    'simhit_y': hit.getPosition()[1],
                    'simhit_z': hit.getPosition()[2],
                    'simhit_px': hit.getMomentum()[0],
                    'simhit_py': hit.getMomentum()[1],
                    'simhit_pz': hit.getMomentum()[2],
                    'simhit_cellid0': hit.getCellID0(),
                    'simhit_t': hit.getTime(),
                    'simhit_inside_bounds': inside_bounds,
                })
                if signal:
                    simhits[-1].update({
                        'simhit_pathlength': hit.getPathLength(),
                        'simhit_distance': distance,
                        'simhit_e': hit.getEDep(),
                    })
                    # 'simhit_pathlength': hit.getPathLength(),
                    # 'simhit_distance': distance,
                    # 'simhit_e': hit.getEDep(),


    # Close
    reader.close()

    # Convert the list of hits to a pandas DataFrame and postprocess
    print("Creating DataFrames ...")
    mcps = pd.DataFrame(mcps)
    simhits = pd.DataFrame(simhits)

    # And postprocess
    print("Postprocessing DataFrames ...")
    mcps = postprocess_mcps(mcps)
    simhits = postprocess_simhits(simhits)

    return mcps, simhits


def postprocess_mcps(df: pd.DataFrame) -> pd.DataFrame:
    df["mcp_p"] = np.sqrt(df["mcp_px"]**2 + df["mcp_py"]**2 + df["mcp_pz"]**2)
    df["mcp_pt"] = np.sqrt(df["mcp_px"]**2 + df["mcp_py"]**2)
    df["mcp_theta"] = np.arctan2(df["mcp_pt"], df["mcp_pz"])
    df["mcp_eta"] = -np.log(np.tan(df["mcp_theta"] / 2))
    df["mcp_phi"] = np.arctan2(df["mcp_py"], df["mcp_px"])
    df["mcp_q_over_pt"] = df["mcp_q"] / df["mcp_pt"]
    df["mcp_vertex_r"] = np.sqrt(df["mcp_vertex_x"]**2 + df["mcp_vertex_y"]**2)
    df["mcp_endpoint_r"] = np.sqrt(df["mcp_endpoint_x"]**2 + df["mcp_endpoint_y"]**2)

    # remove redundant columns
    df.drop(columns=[
        "mcp_px",
        "mcp_py",
        "mcp_theta",
        "mcp_vertex_x",
        "mcp_vertex_y",
        "mcp_endpoint_x",
        "mcp_endpoint_y",
    ], inplace=True)

    # sort columns alphabetically
    return df[sorted(df.columns)]


def postprocess_simhits(df: pd.DataFrame) -> pd.DataFrame:
    signal = df["simhit_signal"].iloc[0]
    print(f"Postprocessing DataFrame, signal={signal} ...")
    df["simhit_r"] = np.sqrt(df["simhit_x"]**2 + df["simhit_y"]**2)
    df["simhit_R"] = np.sqrt(df["simhit_x"]**2 + df["simhit_y"]**2 + df["simhit_z"]**2)
    df["simhit_t_corrected"] = df["simhit_t"] - (df["simhit_R"] / SPEED_OF_LIGHT)
    df["simhit_system"] = np.right_shift(df["simhit_cellid0"], 0) & 0b1_1111
    df["simhit_side"] = np.right_shift(df["simhit_cellid0"], 5) & 0b11
    df["simhit_layer"] = np.right_shift(df["simhit_cellid0"], 7) & 0b11_1111
    df["simhit_module"] = np.right_shift(df["simhit_cellid0"], 13) & 0b111_1111_1111
    df["simhit_sensor"] = np.right_shift(df["simhit_cellid0"], 24) & 0b1111_1111
    df["simhit_layer_div_2"] = df["simhit_layer"] // 2
    df["simhit_layer_mod_2"] = df["simhit_layer"] % 2
    df["simhit_theta"] = np.maximum(np.arctan2(df["simhit_r"], df["simhit_z"]), EPSILON)
    # df["simhit_eta"] = -np.log(np.tan(df["simhit_theta"] / 2))
    # df["simhit_phi"] = np.arctan2(df["simhit_y"], df["simhit_x"])
    # df["simhit_pt"] = np.sqrt(df["simhit_px"]**2 + df["simhit_py"]**2)
    if signal:
        df["simhit_p"] = np.sqrt(df["simhit_px"]**2 + df["simhit_py"]**2 + df["simhit_pz"]**2)
        df["simhit_costheta"] = (df["simhit_x"] * df["simhit_px"] + df["simhit_y"] * df["simhit_py"] + df["simhit_z"] * df["simhit_pz"]) / (df["simhit_R"] * df["simhit_p"])

    # remove unused columns
    drop_cols = [
        "simhit_px",
        "simhit_py",
        "simhit_pz",
        "simhit_R",
    ]
    df.drop(columns=drop_cols, inplace=True)

    # sort columns alphabetically
    return df[sorted(df.columns)]


def sort_mcps(df: pd.DataFrame) -> pd.DataFrame:
    print("Sorting DataFrame ...")
    columns = [
        "file",
        "i_event",
        "i_mcp",
    ]
    return df.sort_values(by=columns).reset_index(drop=True)


def sort_simhits(df: pd.DataFrame) -> pd.DataFrame:
    print("Sorting DataFrame ...")
    columns = [
        "file",
        "i_event",
        "i_mcp",
        "simhit_system",
        "simhit_layer",
        "simhit_module",
        "simhit_sensor",
    ]
    return df.sort_values(by=columns).reset_index(drop=True)


def announce_inside_bounds(df: pd.DataFrame):
    for bounds in [OUTSIDE_BOUNDS, INSIDE_BOUNDS, UNDEFINED_BOUNDS]:
        n_bounds = len(df[df["simhit_inside_bounds"] == bounds])
        print(f"N(simhits) with bounds == {BOUNDS[bounds]}: {n_bounds}")


@contextlib.contextmanager
def silence_c_stdout_stderr():
    # Flush Python buffers
    sys.stdout.flush()
    sys.stderr.flush()

    # Save original FDs
    old_stdout_fd = os.dup(1)
    old_stderr_fd = os.dup(2)

    # Redirect to /dev/null
    with open(os.devnull, "w") as devnull:
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            # Restore original FDs
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)

