import contextlib
import os
import sys
import numpy as np
import pandas as pd
import multiprocessing as mp
import logging
logger = logging.getLogger(__name__)

BYTE_TO_MB = 1e-6
LAYERS = [0, 1]
OUTER_TRACKER_BARREL_COLLECTION = "OuterTrackerBarrelCollection"
COLLECTIONS = [
    OUTER_TRACKER_BARREL_COLLECTION,
]
SPEED_OF_LIGHT = 299.792458  # mm/ns


class HitMaker:

    def __init__(
            self,
            signal: bool,
            slcio_file_paths: list[str],
        ):
        self.slcio_file_paths = slcio_file_paths
        self.signal = signal
        self.df = self.convert()


    def convert(self) -> pd.DataFrame:
        simhits = self.convert_all_files()
        simhits = sort_simhits(simhits)
        memory_usage = simhits.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"simhits.memory_usage: {memory_usage:.1f} MB")
        return simhits


    def convert_all_files(self) -> pd.DataFrame:
        logger.info(f"Converting {len(self.slcio_file_paths)} slcio files to a DataFrame ...")
        processes = min(mp.cpu_count(), len(self.slcio_file_paths))
        with mp.Pool(processes=processes) as pool:
            n_map = len(self.slcio_file_paths)
            file_numbers = list(range(n_map))
            signal = [self.signal]*n_map
            results = pool.starmap(
                convert_one_file,
                zip(self.slcio_file_paths,
                    file_numbers,
                    signal,
                )
            )
        logger.info("Merging DataFrames ...")
        return pd.concat(results, ignore_index=True)


def convert_one_file(
        slcio_file_path: str,
        file_number: int,
        signal: bool,
    ) -> pd.DataFrame:

    # import here to avoid:
    #  - unnecessary imports if not used
    #  - issues with multiprocessing
    with silence_c_stdout_stderr():
        import pyLCIO

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

                if i_hit > 0 and i_hit % 1000000 == 0:
                    logger.info(f"Processing file {os.path.basename(slcio_file_path)} "
                                f"event {i_event} collection {collection} "
                                f"hit {i_hit}/{n_hit} ...")

                # consider a particular set of layers
                layer = np.right_shift(hit.getCellID0(), 7) & 0b11_1111
                if layer not in LAYERS:
                    continue

                # record the hit info
                simhits.append({
                    'file': file_number,
                    'i_event': i_event,
                    'simhit_x': hit.getPosition()[0],
                    'simhit_y': hit.getPosition()[1],
                    'simhit_z': hit.getPosition()[2],
                    'simhit_cellid0': hit.getCellID0(),
                    'simhit_t_corrected': hit.getTime() - (np.sqrt(hit.getPosition()[0]**2 + \
                                                                   hit.getPosition()[1]**2 + \
                                                                   hit.getPosition()[2]**2) / SPEED_OF_LIGHT),
                })

    # Close
    reader.close()

    # Convert the list of hits to a pandas DataFrame and postprocess
    if not signal:
        logger.info("Creating DataFrames ...")
    simhits = pd.DataFrame(simhits)

    # And postprocess
    if not signal:
        logger.info("Postprocessing DataFrames ...")
    simhits = postprocess_simhits(simhits, signal)

    return simhits


def postprocess_simhits(df: pd.DataFrame, signal: bool) -> pd.DataFrame:
    logger.info(f"Postprocessing DataFrame, signal={signal} ...")

    df["simhit_system"] = np.right_shift(df["simhit_cellid0"], 0) & 0b1_1111
    df["simhit_side"] = np.right_shift(df["simhit_cellid0"], 5) & 0b11
    df["simhit_layer"] = np.right_shift(df["simhit_cellid0"], 7) & 0b11_1111
    df["simhit_module"] = np.right_shift(df["simhit_cellid0"], 13) & 0b111_1111_1111
    df["simhit_sensor"] = np.right_shift(df["simhit_cellid0"], 24) & 0b1111_1111
    df["simhit_layer_div_2"] = df["simhit_layer"] // 2
    df["simhit_layer_mod_2"] = df["simhit_layer"] % 2

    # downcast to save memory
    df["file"] = df["file"].astype(np.uint32)
    df["i_event"] = df["i_event"].astype(np.uint32)
    df["simhit_cellid0"] = df["simhit_cellid0"].astype(np.uint32)
    df["simhit_side"] = df["simhit_side"].astype(np.uint8)
    df["simhit_system"] = df["simhit_system"].astype(np.uint8)
    df["simhit_layer"] = df["simhit_layer"].astype(np.uint8)
    df["simhit_layer_div_2"] = df["simhit_layer_div_2"].astype(np.uint8)
    df["simhit_layer_mod_2"] = df["simhit_layer_mod_2"].astype(np.uint8)
    df["simhit_module"] = df["simhit_module"].astype(np.uint16)
    df["simhit_sensor"] = df["simhit_sensor"].astype(np.uint16)
    df["simhit_phi_index"] = df["simhit_module"]
    df["simhit_z_index"] = df["simhit_sensor"]

    # sort columns alphabetically
    return df[sorted(df.columns)]


def sort_simhits(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Sorting DataFrame ...")
    columns = [
        "file",
        "i_event",
        "simhit_system",
        "simhit_layer",
        "simhit_module",
        "simhit_sensor",
    ]
    return df.sort_values(by=columns).reset_index(drop=True)


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

