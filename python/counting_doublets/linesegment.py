import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from constants import DZ_CUT, DR_CUT
from constants import DDZ_CUT, DQOVERPT_CUT, LS_DZ_CUT, LS_DR_CUT
from constants import BYTE_TO_MB

class LineSegment:

    def __init__(self, doublets: pd.DataFrame, signal: bool, cut_line_segments: bool):
        self.signal = signal
        self.cut_line_segments = cut_line_segments
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
        self.doublets["doublet_doublelayer"] = self.doublets["doublet_layer_div_2"]
        self.doublets["doublet_doublelayer_div_2"] = self.doublets["doublet_doublelayer"] // 2
        self.doublets["doublet_doublelayer_mod_2"] = self.doublets["doublet_doublelayer"] % 2

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
        doublelayer = self.doublets["doublet_doublelayer"]
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
            "doublet_doublelayer",
            "doublet_sensor",
            "doublet_module",
        ]
        self.doublets = self.doublets.sort_values(by=cols).reset_index(drop=True)


    def make_linesegments(self):

        groupby_cols = [
            "file",
            "doublet_system",
            "doublet_doublelayer_div_2",
        ] if self.signal else [
            "file",
            "i_event",
            "doublet_system",
            "doublet_doublelayer_div_2",
        ]

        subgroup_cols = [
            "file",
        ] if self.signal else [
            "file",
            "doublet_module",
        ]

        keys = [
            "file",
            "i_event",
            "doublet_system",
            "doublet_doublelayer_div_2",
        ]

        all_cutflows = []
        all_linesegments = []

        for i_group, (cols, df) in enumerate(self.doublets.groupby(groupby_cols)):

            if (self.signal and i_group % 10 == 0) or (not self.signal):
                n_group = len(self.doublets.groupby(groupby_cols))
                logger.info(f"Processing group {i_group} / {n_group} for line segments ...")

            lower = df[ df["doublet_doublelayer_mod_2"] == 0 ]

            # mask_lower = (df["doublet_doublelayer_mod_2"] == 0)
            # mask_upper = (df["doublet_doublelayer_mod_2"] == 1)
            # lower = df[mask_lower]
            # upper = df[mask_upper]

            for i_subgroup, (subcols, subdf) in enumerate(df.groupby(subgroup_cols)):

                n_subgroup = len(df.groupby(subgroup_cols))
                logger.info(f"Processing subgroup {i_subgroup} / {n_subgroup} for line segments ...")

                upper = subdf[ subdf["doublet_doublelayer_mod_2"] == 1 ]

                segments = lower.merge(
                    upper,
                    on=keys,
                    how="inner",
                    validate="many_to_many",
                    suffixes=("_lower", "_upper"),
                )

                # assign i_mcp
                segments["i_mcp"] = segments["i_mcp_lower"].where(segments["i_mcp_lower"] == segments["i_mcp_upper"], -1)

                # assign more features
                segments["linesegment_ddr"] = segments["doublet_dr_upper"] - segments["doublet_dr_lower"]
                segments["linesegment_ddz"] = segments["doublet_dz_upper"] - segments["doublet_dz_lower"]
                segments["linesegment_deta"] = segments["doublet_eta_upper"] - segments["doublet_eta_lower"]
                segments["linesegment_dphi"] = segments["doublet_phi_upper"] - segments["doublet_phi_lower"]
                segments["linesegment_dphi"] = (segments["linesegment_dphi"] + np.pi) % (2 * np.pi) - np.pi
                segments["linesegment_layer_div_4"] = segments["doublet_layer_div_2_lower"] // 2
                segments["linesegment_quadlayer"] = segments["doublet_doublelayer_div_2"]
                segments["linesegment_dqoverpt"] = segments["doublet_qoverpt_upper"] - segments["doublet_qoverpt_lower"]

                # rz projection
                slope_rz = np.divide(segments["doublet_z_upper"] - segments["doublet_z_lower"],
                                     segments["doublet_r_upper"] - segments["doublet_r_lower"])
                segments["linesegment_dz"] = segments["doublet_z_lower"] - segments["doublet_r_lower"] * slope_rz

                # xy projection
                slope_xy = np.divide(segments["doublet_y_upper"] - segments["doublet_y_lower"],
                                     segments["doublet_x_upper"] - segments["doublet_x_lower"])
                intercept_xy = segments["doublet_y_lower"] -  segments["doublet_x_lower"] * slope_xy
                segments["linesegment_dr"] = np.abs(intercept_xy) / np.sqrt(1 + slope_xy**2)

                # record some numbers
                cutflow = {"all": len(segments)}

                # cut some doublets?
                if self.cut_line_segments:
                    # doublelayer = doublets["simhit_layer_div_2"]
                    # mask_dr = np.abs(doublets["doublet_dr"]) < DR_CUT[doublelayer]
                    # mask_dz = np.abs(doublets["doublet_dz"]) < DZ_CUT[doublelayer]
                    # cutflow["dr"] = mask_dr.sum()
                    # cutflow["dz"] = mask_dz.sum()
                    # cutflow["drdz"] = (mask_dr & mask_dz).sum()
                    # doublets = doublets[mask_dr & mask_dz]
                    # DETA_CUT = 0.01
                    # DPHI_CUT = 0.05
                    ql = segments["linesegment_quadlayer"]

                    mask = {}
                    mask["ddz"] = np.abs(segments["linesegment_ddz"]) < DDZ_CUT[ql]
                    mask["dqoverpt"] = np.abs(segments["linesegment_dqoverpt"]) < DQOVERPT_CUT[ql]
                    mask["dz"] = np.abs(segments["linesegment_dz"]) < LS_DZ_CUT[ql]
                    mask["dr"] = np.abs(segments["linesegment_dr"]) < LS_DR_CUT[ql]
                    mask["dphi"] = np.abs(segments["linesegment_dphi"]) < np.pi / 2.0
                    mask["and"] = mask["dz"] & mask["dr"] & mask["dphi"] & mask["dqoverpt"] & mask["ddz"]

                    # mask = (np.abs(segments["linesegment_deta"]) < DETA_CUT[ql]) & (np.abs(segments["linesegment_dphi"]) < DPHI_CUT[ql])
                    for cut in mask.keys():
                        cutflow[cut] = np.sum(mask[cut])

                    segments = segments[mask["and"]]

                    # cutflow["deta"] = np.sum(mask_deta)
                    # cutflow["dphi"] = np.sum(mask_dphi)
                    # cutflow["ddr"] = np.sum(mask_ddr)
                    # cutflow["ddz"] = np.sum(mask_ddz)
                    # cutflow["deta_dphi"] = np.sum(mask)
                    # segments = segments[mask]

                # stats from this group
                logger.info(f"Processed subgroup {i_subgroup} / {n_subgroup} which has {len(segments)} line segments ...")

                # save them
                all_cutflows.append(cutflow)
                all_linesegments.append(segments)

        # merge them
        logger.info(f"Merging {len(all_linesegments)} groups of line segments ...")
        self.df = pd.concat(all_linesegments, ignore_index=True)
        memory = self.df.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage of line segments: {memory:.1f} MB")

        # cutflow
        cutflow = pd.DataFrame(all_cutflows)
        for col in cutflow.columns:
            logger.info(f"Line segments cutflow, {col}: {cutflow[col].sum()}")

        # with pd.option_context("display.min_rows", 50, "display.max_rows", 50):
        #     logger.info("Line segments after merging doublets:")
        #     logger.info(f"\n{self.df}")

