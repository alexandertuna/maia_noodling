import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from constants import MD_DZ_CUT, MD_DR_CUT
from constants import LS_DDZ_CUT, LS_DQOVERPT_CUT, LS_DZ_CUT, LS_DR_CUT
from constants import LS_DTHETA_RZ_CUT, LS_DTHETA_XY_CUT
from constants import BYTE_TO_MB, NO_MCP

class LineSegment:

    #
    # To make doublets, we do 2 groupbys:
    #  Layers 01, 23, ... grouped by doublet_doublelayer_mod_2
    #  Layers 12, 34, ... grouped by doublet_doublelayer_plus_1_mod_2
    #

    def __init__(self, doublets: pd.DataFrame, signal: bool, cut_line_segments: bool):
        self.df = None
        self.signal = signal
        self.cut_line_segments = cut_line_segments
        self.lower_suffix = "lower"
        self.upper_suffix = "upper"
        memory = doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Making linesegments with doublets memory {memory:.1f} MB ...")
        self.doublets = doublets.copy()
        self.add_remove_columns_from_doublets()
        self.filter_doublets()
        self.sort_doublets()
        self.make_linesegments()


    def add_remove_columns_from_doublets(self):

        # add columns for 2 groupbys
        self.doublets["doublet_doublelayer_div_2"] = self.doublets["doublet_doublelayer"] // 2
        self.doublets["doublet_doublelayer_mod_2"] = self.doublets["doublet_doublelayer"] % 2
        self.doublets["doublet_doublelayer_plus_1"] = self.doublets["doublet_doublelayer"] + 1
        self.doublets["doublet_doublelayer_plus_1_div_2"] = self.doublets["doublet_doublelayer_plus_1"] // 2
        self.doublets["doublet_doublelayer_plus_1_mod_2"] = self.doublets["doublet_doublelayer_plus_1"] % 2

        # prepare to drop columns after finding line segments
        self.dropcols = [
            "doublet_doublelayer_div_2",
            "doublet_doublelayer_mod_2",
            "doublet_doublelayer_plus_1",
            "doublet_doublelayer_plus_1_div_2",
            "doublet_doublelayer_plus_1_mod_2",
        ]
        for col in self.dropcols.copy():
            self.dropcols.append(f"{col}_{self.lower_suffix}")
            self.dropcols.append(f"{col}_{self.upper_suffix}")
        # if not self.signal:
        for coord in ["x", "y", "z", "r", "p", "t_corrected", "costheta"]:
            for simhit_suffix in [self.lower_suffix, self.upper_suffix]:
                for doublet_suffix in [self.lower_suffix, self.upper_suffix]:
                    self.dropcols.append(f"simhit_{coord}_{simhit_suffix}_{doublet_suffix}")

        # announce memory
        memory = self.doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage after adding/removing columns: {memory:.1f} MB")


    def filter_doublets(self):
        # only consider "good" doublets
        logger.info("Filtering doublets for line segments ...")
        doublelayer = self.doublets["doublet_doublelayer"]
        self.doublets = self.doublets[
            (np.abs(self.doublets["doublet_dz"]) < MD_DZ_CUT[doublelayer]) &
            (np.abs(self.doublets["doublet_dr"]) < MD_DR_CUT[doublelayer])
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
        logger.info("Making line segments ...")

        # two loops:
        # layers 01, 23, 45, ... (even)
        # layers 12, 34, 56, ... (odd)
        even, odd = 0, 1

        groupby_cols = {
            even: [
                "file",
                "doublet_system",
                "doublet_doublelayer_div_2",
            ] if self.signal else [
                "file",
                "i_event",
                "doublet_system",
                "doublet_doublelayer_div_2",
            ],
            odd: [
                "file",
                "doublet_system",
                "doublet_doublelayer_plus_1_div_2",
            ] if self.signal else [
                "file",
                "i_event",
                "doublet_system",
                "doublet_doublelayer_plus_1_div_2",
            ],
        }

        subgroup_cols = [
            "file",
        ] if self.signal else [
            "file",
            "doublet_module",
        ]

        keys = {
            even: [
                "file",
                "i_event",
                "doublet_system",
                "doublet_doublelayer_div_2",
            ],
            odd: [
                "file",
                "i_event",
                "doublet_system",
                "doublet_doublelayer_plus_1_div_2",
            ],
        }

        lower_vs_upper = {
            even: "doublet_doublelayer_mod_2",
            odd: "doublet_doublelayer_plus_1_mod_2",
        }

        all_cutflows = []
        all_linesegments = []

        for start in [even, odd]:

            for i_group, (cols, df) in enumerate(self.doublets.groupby(groupby_cols[start])):

                # progress bar
                if (self.signal and i_group % 10 == 0) or (not self.signal):
                    n_group = len(self.doublets.groupby(groupby_cols[start]))
                    logger.info(f"Processing group {i_group} / {n_group} for line segments ...")

                # get lower doublets
                lower = df[ df[lower_vs_upper[start]] == 0 ]

                # get upper doublets
                n_subgroup = len(df.groupby(subgroup_cols))
                for i_subgroup, (subcols, subdf) in enumerate(df.groupby(subgroup_cols)):

                    upper = subdf[ subdf[lower_vs_upper[start]] == 1 ]

                    # progress bar
                    if i_subgroup > 0 and i_subgroup % 10 == 0:
                        logger.info(f"Processing subgroup {i_subgroup} / {n_subgroup} for line segments ...")

                    # get all combinations of lower and upper
                    segments = lower.merge(
                        upper,
                        on=keys[start],
                        how="inner",
                        validate="many_to_many",
                        suffixes=("_lower", "_upper"),
                    )

                    # assign truth info
                    segments["i_mcp"] = segments["i_mcp_lower"].where(segments["i_mcp_lower"] == segments["i_mcp_upper"], NO_MCP)
                    segments["ls_first_exit"] = segments["doublet_first_exit_lower"] & segments["doublet_first_exit_upper"]

                    # rename some things
                    rename = {
                        "doublet_system": "ls_system",
                    }
                    segments = segments.rename(columns=rename)

                    # assign more features
                    segments["ls_ddr"] = segments["doublet_dr_upper"] - segments["doublet_dr_lower"]
                    segments["ls_ddz"] = segments["doublet_dz_upper"] - segments["doublet_dz_lower"]
                    segments["ls_deta"] = segments["doublet_eta_upper"] - segments["doublet_eta_lower"]
                    segments["ls_dphi"] = segments["doublet_phi_upper"] - segments["doublet_phi_lower"]
                    segments["ls_dphi"] = (segments["ls_dphi"] + np.pi) % (2 * np.pi) - np.pi
                    segments["ls_dqoverpt"] = segments["doublet_qoverpt_upper"] - segments["doublet_qoverpt_lower"]
                    segments["ls_doublelayer"] = segments["doublet_doublelayer_lower"]

                    # rz projection
                    slope_rz = np.divide(segments["doublet_z_upper"] - segments["doublet_z_lower"],
                                         segments["doublet_r_upper"] - segments["doublet_r_lower"])
                    segments["ls_dz"] = segments["doublet_z_lower"] - segments["doublet_r_lower"] * slope_rz

                    # xy projection
                    slope_xy = np.divide(segments["doublet_y_upper"] - segments["doublet_y_lower"],
                                         segments["doublet_x_upper"] - segments["doublet_x_lower"])
                    intercept_xy = segments["doublet_y_lower"] - segments["doublet_x_lower"] * slope_xy
                    segments["ls_dr"] = np.abs(intercept_xy) / np.sqrt(1 + slope_xy**2)

                    # angle differences (handle wraparound)
                    segments["ls_dtheta_rz"] = segments["doublet_theta_rz_upper"] - segments["doublet_theta_rz_lower"]
                    segments["ls_dtheta_xy"] = segments["doublet_theta_xy_upper"] - segments["doublet_theta_xy_lower"]
                    segments["ls_dtheta_rz"] = (segments["ls_dtheta_rz"] + np.pi) % (2 * np.pi) - np.pi
                    segments["ls_dtheta_xy"] = (segments["ls_dtheta_xy"] + np.pi) % (2 * np.pi) - np.pi

                    # drop cols which were only necessary for this step
                    segments.drop(columns=self.dropcols, errors="ignore", inplace=True)

                    # record some numbers
                    cutflow = {"all": len(segments)}

                    # cut some doublets?
                    if self.cut_line_segments:
                        dl = segments["ls_doublelayer"]
                        mask = {}
                        mask["ddz"] = np.abs(segments["ls_ddz"]) < LS_DDZ_CUT[dl]
                        mask["dqoverpt"] = np.abs(segments["ls_dqoverpt"]) < LS_DQOVERPT_CUT[dl]
                        mask["dtheta_rz"] = np.abs(segments["ls_dtheta_rz"]) < LS_DTHETA_RZ_CUT[dl]
                        mask["dtheta_xy"] = np.abs(segments["ls_dtheta_xy"]) < LS_DTHETA_XY_CUT[dl]
                        mask["dz"] = np.abs(segments["ls_dz"]) < LS_DZ_CUT[dl]
                        mask["dr"] = np.abs(segments["ls_dr"]) < LS_DR_CUT[dl]
                        mask["dphi"] = np.abs(segments["ls_dphi"]) < np.pi / 2.0
                        # mask["and"] = mask["dz"] & mask["dr"] & mask["dphi"] & mask["dqoverpt"] & mask["ddz"]
                        mask["drdz"] = mask["dz"] & mask["dr"] & mask["dphi"]
                        mask["drdzdthetarz"] = mask["dz"] & mask["dr"] & mask["dphi"] & mask["dtheta_rz"]
                        mask["and"] = mask["dz"] & mask["dr"] & mask["dphi"] & mask["dtheta_rz"] & mask["dtheta_xy"]
                        for cut in mask.keys():
                            cutflow[cut] = np.sum(mask[cut])
                        segments = segments[mask["and"]]

                    # stats from this group
                    if i_subgroup > 0 and i_subgroup % 10 == 0:
                        logger.info(f"Processed subgroup {i_subgroup} / {n_subgroup} which has {len(segments)} line segments ...")

                    # save them
                    all_cutflows.append(cutflow)
                    all_linesegments.append(segments)

        # merge them
        logger.info(f"Merging {len(all_linesegments)} groups of line segments ...")
        self.df = pd.concat(all_linesegments, ignore_index=True)

        # sort them
        sortby = [
            "file",
            "i_event",
            "i_mcp",
            "ls_doublelayer",
        ]
        self.df = self.df.sort_values(by=sortby).reset_index(drop=True)

        # announce memory
        memory = self.df.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage of line segments: {memory:.1f} MB")

        # cutflow
        cutflow = pd.DataFrame(all_cutflows)
        for col in cutflow.columns:
            logger.info(f"Line segments cutflow, {col}: {cutflow[col].sum()}")


