import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from constants import DZ_CUT, DR_CUT
from constants import SYSTEMS, DOUBLELAYERS
from constants import BYTE_TO_MB

class LineSegment:

    def __init__(self, doublets: pd.DataFrame, signal: bool):
        self.signal = signal
        memory = doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Making linesegments with doublets memory {memory:.1f} MB ...")
        self.doublets = doublets.copy()
        self.add_remove_columns_from_doublets()
        self.filter_doublets()
        self.sort_doublets()
        self.make_linesegments()


    def add_remove_columns_from_doublets(self):
        # add columns
        # self.doublets["doublet_r"] = (self.doublets["simhit_r_lower"] + self.doublets["simhit_r_upper"]) / 2
        # self.doublets["doublet_z"] = (self.doublets["simhit_z_lower"] + self.doublets["simhit_z_upper"]) / 2
        # self.doublets["doublet_x"] = (self.doublets["simhit_x_lower"] + self.doublets["simhit_x_upper"]) / 2
        # self.doublets["doublet_y"] = (self.doublets["simhit_y_lower"] + self.doublets["simhit_y_upper"]) / 2
        # self.doublets["doublet_phi"] = np.arctan2(self.doublets["doublet_y"], self.doublets["doublet_x"])
        # self.doublets["doublet_theta"] = np.arctan2(self.doublets["doublet_r"], self.doublets["doublet_z"])
        # self.doublets["doublet_eta"] = -np.log(np.tan(self.doublets["doublet_theta"] / 2))

        # rename columns
        rename = {
            "simhit_system": "doublet_system",
            "simhit_layer_div_2": "doublet_layer_div_2",
            "simhit_sensor": "doublet_sensor",
            "simhit_module": "doublet_module",
        }
        self.doublets = self.doublets.rename(columns=rename)

        # remove columns
        # cols = [
        #     "simhit_r_lower",
        #     "simhit_r_upper",
        #     "simhit_x_lower",
        #     "simhit_x_upper",
        #     "simhit_y_lower",
        #     "simhit_y_upper",
        #     "simhit_z_lower",
        #     "simhit_z_upper",
        #     # "simhit_p_lower",
        #     # "simhit_p_upper",
        #     # "simhit_costheta_lower",
        #     # "simhit_costheta_upper",
        #     # "simhit_t_corrected_lower",
        #     # "simhit_t_corrected_upper",
        #     "doublet_r",
        #     "doublet_z",
        #     "doublet_x",
        #     "doublet_y",
        # ]
        # self.doublets = self.doublets.drop(columns=cols)
        memory = self.doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage after adding/removing columns: {memory:.1f} MB")


    def filter_doublets(self):
        # only consider "good" doublets
        logger.info("Filtering doublets for line segments ...")
        doublelayer = self.doublets["doublet_layer_div_2"]
        self.doublets = self.doublets[
            (self.doublets["doublet_dz"] < DZ_CUT[doublelayer]) &
            (self.doublets["doublet_dr"] < DR_CUT[doublelayer])
        ]
        memory = self.doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage after filtering doublets: {memory:.1f} MB")


    def sort_doublets(self):
        # sort doublets by file, event, system, doublelayer, sensor, module
        logger.info("Sorting doublets for line segments ...")
        cols = [
            "file",
            "i_event",
            "doublet_system",
            "doublet_layer_div_2",
            "doublet_sensor",
            "doublet_module",
        ]
        self.doublets = self.doublets.sort_values(by=cols).reset_index(drop=True)


    def make_linesegments(self):

        groupby_cols = [
            "file",
        ]

        keys = [
            "file",
            "i_event",
            "doublet_system",
        ]

        linesegments = []

        for group, df in self.doublets.groupby(groupby_cols):

            #
            # I dont like this doublelayer logic
            # I will replace it with doublet_layer_div_2 and doublet_layer_mod_2
            #
            for doublelayer in DOUBLELAYERS:

                if doublelayer % 2 != 0:
                    continue

                mask_lower = (df["doublet_layer_div_2"] == doublelayer)
                mask_upper = (df["doublet_layer_div_2"] == doublelayer + 1)

                lower = df[mask_lower]
                upper = df[mask_upper]
                segments = lower.merge(
                    upper,
                    on=keys,
                    how="inner",
                    validate="many_to_many",
                    suffixes=("_lower", "_upper"),
                )

                # assign i_mcp
                segments["i_mcp"] = segments["i_mcp_lower"].where(segments["i_mcp_lower"] == segments["i_mcp_upper"], -1)
                segments["linesegment_deta"] = segments["doublet_eta_upper"] - segments["doublet_eta_lower"]
                segments["linesegment_dphi"] = segments["doublet_phi_upper"] - segments["doublet_phi_lower"]
                segments["linesegment_dphi"] = (segments["linesegment_dphi"] + np.pi) % (2 * np.pi) - np.pi
                segments["linesegment_layer_div_4"] = segments["doublet_layer_div_2_lower"] // 2

                # mcp_match = (
                #     (segments["i_mcp_lower_lower"] == segments["i_mcp_lower_upper"]) &
                #     (segments["i_mcp_lower_lower"] == segments["i_mcp_upper_lower"]) &
                #     (segments["i_mcp_lower_lower"] == segments["i_mcp_upper_upper"])
                # )
                # segments["i_mcp"] = segments["i_mcp_lower_lower"].where(mcp_match, -1)
                # segments.drop(columns=[
                #     "i_mcp_lower_lower",
                #     "i_mcp_lower_upper",
                #     "i_mcp_upper_lower",
                #     "i_mcp_upper_upper",
                # ], inplace=True)
                # segments["linesegment_deta"] = segments["doublet_eta_upper"] - segments["doublet_eta_lower"]
                # segments["linesegment_dphi"] = segments["doublet_phi_upper"] - segments["doublet_phi_lower"]
                # segments["linesegment_layer_div_4"] = segments["doublet_layer_div_2_lower"] // 2

                linesegments.append(segments)

        self.df = pd.concat(linesegments, ignore_index=True)
        memory = self.df.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage of line segments: {memory:.1f} MB")

        with pd.option_context("display.min_rows", 50, "display.max_rows", 50):
            logger.info("Line segments after merging doublets:")
            logger.info(f"\n{self.df}")

