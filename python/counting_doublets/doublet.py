import numpy as np
import pandas as pd
import time
import logging
logger = logging.getLogger(__name__)

class DoubletMaker:


    def __init__(self, signal: bool, simhits: pd.DataFrame):
        self.signal = signal
        self.df = self.make_doublets(simhits)


    def make_doublets(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Making doublets ...")
        doublelayer_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
        ]
        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_module", # the phi-module
            "simhit_sensor", # the z-sensor
        ]

        simhit_attrs_to_propagate = [
            "i_mcp",
            "simhit_r",
            "simhit_z",
            "simhit_x",
            "simhit_y",
        ]
        if self.signal:
            simhit_attrs_to_propagate += [
                "simhit_t_corrected",
                "simhit_p",
                "simhit_costheta",
            ]
        lower_cols = doublet_cols + [ f"{attr}_lower" for attr in simhit_attrs_to_propagate ]
        upper_cols = doublet_cols + [ f"{attr}_upper" for attr in simhit_attrs_to_propagate ]
        lower_cols_rename = { attr: f"{attr}_lower" for attr in simhit_attrs_to_propagate }
        upper_cols_rename = { attr: f"{attr}_upper" for attr in simhit_attrs_to_propagate }

        doublets_list = []
        # groups = df.groupby(doublet_cols)
        groups = df.groupby(doublelayer_cols)
        for i_group, (cols, group) in enumerate(groups):

            if len(group) < 3:
                continue
            if self.signal:
                if i_group % 1000 == 0:
                    logger.info(f"Processing group {i_group+1}/{len(groups)} at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
            else:
                logger.info(f"Processing group {i_group+1}/{len(groups)} at {time.strftime('%Y-%m-%d %H:%M:%S')}...")

            lower_mask = group["simhit_layer_mod_2"] == 0
            upper_mask = group["simhit_layer_mod_2"] == 1

            # logger.info("Getting lower and upper hits ...")
            lower = group[lower_mask].rename(columns=lower_cols_rename)[lower_cols]
            upper = group[upper_mask].rename(columns=upper_cols_rename)[upper_cols]

            # inner join to find doublets
            # logger.info("Joining ...")
            doublets = lower.merge(upper, on=doublet_cols, how="inner")

            # rz
            slope = np.divide(doublets["simhit_z_upper"] - doublets["simhit_z_lower"],
                              doublets["simhit_r_upper"] - doublets["simhit_r_lower"])
            doublets["intercept_rz"] = doublets["simhit_z_lower"] - doublets["simhit_r_lower"] * slope

            # xy
            phi_local = np.arctan2(doublets["simhit_y_upper"] - doublets["simhit_y_lower"],
                                   doublets["simhit_x_upper"] - doublets["simhit_x_lower"])
            phi_global = np.arctan2((doublets["simhit_y_lower"] + doublets["simhit_y_upper"]) / 2.0,
                                    (doublets["simhit_x_lower"] + doublets["simhit_x_upper"]) / 2.0)
            doublets["dphi"] = phi_local - phi_global
            doublets["dphi"] = (doublets["dphi"] + np.pi) % (2 * np.pi) - np.pi

            doublets_list.append(doublets)


        if len(doublets_list) == 0:
            raise ValueError("No doublets found in the DataFrame")

        return pd.concat(doublets_list, ignore_index=True)
