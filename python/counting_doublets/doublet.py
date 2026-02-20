import numpy as np
import pandas as pd
import time
import logging
logger = logging.getLogger(__name__)

from constants import DZ_CUT, DR_CUT

BYTE_TO_MB = 1e-6

class DoubletMaker:


    def __init__(self, signal: bool, cut_doublets: bool, simhits: pd.DataFrame):
        self.signal = signal
        self.cut_doublets = cut_doublets
        self.df = self.make_doublets(simhits)


    def make_doublets(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Making doublets ...")
        groupby_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
        ]
        if not self.signal:
            groupby_cols += [
                "simhit_module", # the phi-module
                "simhit_sensor", # the z-sensor
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

        drop_cols = [
            "simhit_z_upper",
            "simhit_z_lower",
            "simhit_r_upper",
            "simhit_r_lower",
            "simhit_x_upper",
            "simhit_x_lower",
            "simhit_y_upper",
            "simhit_y_lower",
            "i_mcp_upper",
            "i_mcp_lower",
        ]

        lower_cols = doublet_cols + [ f"{attr}_lower" for attr in simhit_attrs_to_propagate ]
        upper_cols = doublet_cols + [ f"{attr}_upper" for attr in simhit_attrs_to_propagate ]
        lower_cols_rename = { attr: f"{attr}_lower" for attr in simhit_attrs_to_propagate }
        upper_cols_rename = { attr: f"{attr}_upper" for attr in simhit_attrs_to_propagate }

        n_upper, n_lower = 0, 0

        def make_doublets_from_group(group: pd.DataFrame) -> pd.DataFrame:

            lower_mask = group["simhit_layer_mod_2"] == 0
            upper_mask = group["simhit_layer_mod_2"] == 1

            # logger.info("Getting lower and upper hits ...")
            lower = group[lower_mask].rename(columns=lower_cols_rename)[lower_cols]
            upper = group[upper_mask].rename(columns=upper_cols_rename)[upper_cols]
            # n_lower += len(lower)
            # n_upper += len(upper)

            # inner join to find doublets
            doublets = lower.merge(upper, on=doublet_cols, how="inner")
            # sizes[0] = int(doublets.memory_usage(deep=True).sum() * BYTE_TO_MB)

            # rz
            slope = np.divide(doublets["simhit_z_upper"] - doublets["simhit_z_lower"],
                              doublets["simhit_r_upper"] - doublets["simhit_r_lower"])
            doublets["intercept_rz"] = doublets["simhit_z_lower"] - doublets["simhit_r_lower"] * slope

            # xy: dphi
            phi_local = np.arctan2(doublets["simhit_y_upper"] - doublets["simhit_y_lower"],
                                   doublets["simhit_x_upper"] - doublets["simhit_x_lower"])
            phi_global = np.arctan2((doublets["simhit_y_lower"] + doublets["simhit_y_upper"]) / 2.0,
                                    (doublets["simhit_x_lower"] + doublets["simhit_x_upper"]) / 2.0)
            doublets["dphi"] = phi_local - phi_global
            doublets["dphi"] = (doublets["dphi"] + np.pi) % (2 * np.pi) - np.pi

            # xy: dr at point of closest approach to origin
            slope_xy = np.divide(doublets["simhit_y_upper"] - doublets["simhit_y_lower"],
                                 doublets["simhit_x_upper"] - doublets["simhit_x_lower"])
            intercept_xy = doublets["simhit_y_lower"] - slope_xy * doublets["simhit_x_lower"]
            doublets["dr"] = np.abs(intercept_xy) / np.sqrt(1 + slope_xy**2)

            # drop columns which arent used downstream
            if not self.signal:
                doublets.drop(columns=drop_cols, inplace=True)
                # sizes[1] = int(doublets.memory_usage(deep=True).sum() * BYTE_TO_MB)

            # record some numbers
            cutflow = {"all": len(doublets)}

            # cut some doublets?
            if self.cut_doublets:
                mask_dr = np.abs(doublets["dr"]) < DR_CUT
                mask_dz = np.abs(doublets["intercept_rz"]) < DZ_CUT
                cutflow["dr"] = mask_dr.sum()
                cutflow["dz"] = mask_dz.sum()
                cutflow["drdz"] = (mask_dr & mask_dz).sum()
                doublets = doublets[mask_dr & mask_dz]

            return doublets, cutflow



        groups = df.groupby(groupby_cols)
        all_doublets, all_cutflows = [], []

        for i_group, (cols, group) in enumerate(groups):

            doublets, cutflow = make_doublets_from_group(group)
            size = doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
            length = len(doublets)

            all_doublets.append(doublets)
            all_cutflows.append(cutflow)

            if (self.signal and i_group % 1000 == 0) or not self.signal:
                logger.info(f"Processed group {i_group}/{len(groups)}, doublet size = {size:.1f} MB, n(doublets) = {length} ...")

            # lower_mask = group["simhit_layer_mod_2"] == 0
            # upper_mask = group["simhit_layer_mod_2"] == 1

            # # logger.info("Getting lower and upper hits ...")
            # lower = group[lower_mask].rename(columns=lower_cols_rename)[lower_cols]
            # upper = group[upper_mask].rename(columns=upper_cols_rename)[upper_cols]
            # n_lower += len(lower)
            # n_upper += len(upper)

            # # inner join to find doublets
            # if i_group == 0 and not self.signal:
            #     logger.info("Joining to make doublets ...")
            # doublets = lower.merge(upper, on=doublet_cols, how="inner")
            # sizes[0] = int(doublets.memory_usage(deep=True).sum() * BYTE_TO_MB)

            # # mention memory usage
            # if i_group == 0 and not self.signal:
            #     buf = io.StringIO()
            #     doublets.info(memory_usage='deep', buf=buf)
            #     logger.info(f"doublets.info\n{buf.getvalue()}")

            # # rz
            # if i_group == 0 and not self.signal:
            #     logger.info("Adding derived doublet quantities ...")
            # slope = np.divide(doublets["simhit_z_upper"] - doublets["simhit_z_lower"],
            #                   doublets["simhit_r_upper"] - doublets["simhit_r_lower"])
            # doublets["intercept_rz"] = doublets["simhit_z_lower"] - doublets["simhit_r_lower"] * slope

            # # xy: dphi
            # phi_local = np.arctan2(doublets["simhit_y_upper"] - doublets["simhit_y_lower"],
            #                        doublets["simhit_x_upper"] - doublets["simhit_x_lower"])
            # phi_global = np.arctan2((doublets["simhit_y_lower"] + doublets["simhit_y_upper"]) / 2.0,
            #                         (doublets["simhit_x_lower"] + doublets["simhit_x_upper"]) / 2.0)
            # doublets["dphi"] = phi_local - phi_global
            # doublets["dphi"] = (doublets["dphi"] + np.pi) % (2 * np.pi) - np.pi

            # # xy: dr at point of closest approach to origin
            # slope_xy = np.divide(doublets["simhit_y_upper"] - doublets["simhit_y_lower"],
            #                      doublets["simhit_x_upper"] - doublets["simhit_x_lower"])
            # intercept_xy = doublets["simhit_y_lower"] - slope_xy * doublets["simhit_x_lower"]
            # doublets["dr"] = np.abs(intercept_xy) / np.sqrt(1 + slope_xy**2)

            # # drop columns which arent used downstream
            # if not self.signal:
            #     doublets.drop(columns=drop_cols, inplace=True)
            #     sizes[1] = int(doublets.memory_usage(deep=True).sum() * BYTE_TO_MB)

            # doublets_list.append(doublets)

        doublets = pd.concat(all_doublets, ignore_index=True)
        cutflow = pd.DataFrame(all_cutflows)
        for col in cutflow.columns:
            logger.info(f"Doublets cutflow, {col}: {cutflow[col].sum()}")

        if len(doublets) == 0:
            raise ValueError("No doublets found in the DataFrame")

        logger.info(f"Total lower hits for doublets: {n_lower}")
        logger.info(f"Total upper hits for doublets: {n_upper}")
        logger.info(f"Concatenating doublets ...")

        return doublets
