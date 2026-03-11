import numpy as np
import pandas as pd
from memory_profiler import memory_usage
import logging
logger = logging.getLogger(__name__)

BYTE_TO_MB = 1e-6
DZ_CUT = 22 # mm
DR_CUT = 260 # mm


class DoubletMaker:

    def __init__(self, signal: bool, cut: bool, simhits: pd.DataFrame):
        self.signal = signal
        self.cut = cut
        self.df = self.make_doublets(simhits)


    def make_doublets(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Making doublets ...")

        groupby_cols = [
            "file",
        ]
        if not self.signal:
            groupby_cols += [
                "i_event", # the event
                "simhit_system", # the system (IT, OT)
                "simhit_layer_div_2", # the double layer
                "simhit_phi_index",
                # "simhit_z_index",
            ]

        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_phi_index",
            "simhit_z_index",
        ]

        def make_doublets_from_group(group: pd.DataFrame) -> pd.DataFrame:

            # get lower and upper hits
            lower = group[ group["simhit_layer_mod_2"] == 0 ]
            upper = group[ group["simhit_layer_mod_2"] == 1 ]

            def run_merge():
               return pd.merge(lower, upper, on=doublet_cols, how="inner", suffixes=("_lower", "_upper"))

            baseline = memory_usage(-1, interval=0.1, timeout=1)[0]
            peak, doublets = memory_usage(
                (run_merge, ),
                retval=True,
                max_usage=True,
            )
            peak -= baseline
            logger.info(f"Memory usage during merge: {peak:.1f} MB")

            # filter?
            if self.cut:
                raise NotImplementedError("Cutting doublets is not implemented yet")
                mask_dr = np.abs(doublets["doublet_dr"]) < DR_CUT
                mask_dz = np.abs(doublets["doublet_dz"]) < DZ_CUT
                doublets = doublets[mask_dr & mask_dz]

            return doublets, peak


        groups = df.groupby(groupby_cols)
        all_doublets = []
        total_peak = 0

        for i_group, (cols, group) in enumerate(groups):

            doublets, peak = make_doublets_from_group(group)
            total_peak += peak
            size = doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
            length = len(doublets)
            all_doublets.append(doublets)

            if (self.signal and i_group % 100 == 0) or (not self.signal and i_group % 100 == 0):
                logger.info(f"Processed group {i_group}/{len(groups)}, doublet size = {size:.1f} MB, n(doublets) = {length} ...")

        doublets = pd.concat(all_doublets, ignore_index=True)
        size = doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Made {len(doublets)} doublets with size {size:.1f} MB. Total peak {total_peak:.1f} MB")
        return doublets
