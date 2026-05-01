"""
This module defines the QuadDoublet class, which creates a quad doublet from two line segments.
All line segments in layers 0-3 are considered for combination with line segments in layer 4-7.
The line segments are combined if they satisfy goodness criteria.
To avoid filling the memory with all possible combinations, combination is done with a groupby approach.

"""

import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from constants import BYTE_TO_MB, NO_MCP

class QuadDoublet:

    def __init__(self, linesegments: pd.DataFrame, signal: bool, cut_quad_doublets: bool):
        self.df = None
        self.signal = signal
        self.cut_quad_doublets = cut_quad_doublets
        self.linesegments = linesegments.copy()
        memory = self.linesegments.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Making quad doublets. Line segments dataframe size: {memory:.2f} MB")
        self.prep_linesegments()
        self.make_quad_doublets()


    def prep_linesegments(self) -> None:
        logger.info("Preprocessing line segments for quad doublet making ...")


    def make_quad_doublets(self) -> None:
        logger.info("Making quad doublets ...")

        # one loop for now:
        # layers 0123 combined with layers 4567
        # equivalently, doublelayers 01 combined with 23 (doublelayer // 4 == 0)

        groupby_cols = [
            "file",
            "ls_system",
            "ls_doublelayer_div_4",
            "ls_doublelayer_even",
        ]
        n_group = len(self.linesegments.groupby(groupby_cols))

        subgroup_cols = [
            "file",
        ] if self.signal else [
            "file",
            "ls_module",
        ]

        merge_keys = [
            "file",
            "i_event",
            "ls_system",
            "ls_doublelayer_div_4",
        ]

        for i_group, (cols, df) in enumerate(self.linesegments.groupby(groupby_cols)):
            logger.info(f"Processing group {i_group} / {n_group} for quaddoublets (n={len(df)}) ...")
            if len(df) == 0:
                continue
            logger.info(cols)

            lower = df[df["ls_doublelayer_mod_4"] == 0]
            upper = df[df["ls_doublelayer_mod_4"] == 2]
            logger.info(f"Lower: {len(lower)}, Upper: {len(upper)}")

            for i_subgroup, (subcols, subdf) in enumerate(df.groupby(subgroup_cols)):

                upper = subdf[ subdf["ls_doublelayer_mod_4"] > 0 ]

                # get all combinations of lower and upper
                qds = lower.merge(
                    upper,
                    on=merge_keys,
                    how="inner",
                    validate="many_to_many",
                    suffixes=("_lower", "_upper"),
                )
                logger.info(f"Lower: {len(lower)}, Upper: {len(upper)}, Combos: {len(qds)}")

                # rz projection
                slope_rz = np.divide(qds["ls_z_upper"] - qds["ls_z_lower"],
                                     qds["ls_r_upper"] - qds["ls_r_lower"])
                qds["ls_z"] = qds["ls_z_lower"] - qds["ls_r_lower"] * slope_rz

                # xy projection
                slope_xy = np.divide(qds["ls_y_upper"] - qds["ls_y_lower"],
                                     qds["ls_x_upper"] - qds["ls_x_lower"])
                intercept_xy = qds["ls_y_lower"] - qds["ls_x_lower"] * slope_xy
                qds["qd_dr"] = np.abs(intercept_xy) / np.sqrt(1 + slope_xy**2)

                # assign truth info
                mcp_ok = qds["i_mcp_lower"] == qds["i_mcp_upper"]
                qds["i_mcp"] = qds["i_mcp_lower"].where(mcp_ok, NO_MCP)
                if self.signal:
                    qds["qd_first_exit"] = qds["ls_first_exit_lower"] & qds["ls_first_exit_upper"]
                    for attr in [
                        "mcp_pt",
                        "mcp_eta",
                        "mcp_phi",
                        "mcp_pdg",
                        "mcp_q",
                        "mcp_vertex_r",
                        "mcp_vertex_z",
                        "mcp_qoverpt",
                    ]:
                        qds[attr] = qds[f"{attr}_lower"].where(mcp_ok, 0)

                # pass-through the simhit positions
                for coord in ["x", "y", "r"]:
                    qds[f"qd_{coord}_0"] = qds[f"ls_{coord}_0_lower"]
                    qds[f"qd_{coord}_1"] = qds[f"ls_{coord}_1_lower"]
                    qds[f"qd_{coord}_2"] = qds[f"ls_{coord}_2_lower"]
                    qds[f"qd_{coord}_3"] = qds[f"ls_{coord}_3_lower"]
                    qds[f"qd_{coord}_4"] = qds[f"ls_{coord}_0_upper"]
                    qds[f"qd_{coord}_5"] = qds[f"ls_{coord}_1_upper"]
                    qds[f"qd_{coord}_6"] = qds[f"ls_{coord}_2_upper"]
                    qds[f"qd_{coord}_7"] = qds[f"ls_{coord}_3_upper"]

                # find the circle (radius, x_center, y_center) formed from the first three hits
                BAD_CHI2 = 1e6
                i0, i1, i2 = 0, 4, 7
                ixs = [1, 2, 3, 5, 6]
                circle_d = 2 * (qds[f"qd_x_{i0}"] * (qds[f"qd_y_{i1}"] - qds[f"qd_y_{i2}"]) +
                                qds[f"qd_x_{i1}"] * (qds[f"qd_y_{i2}"] - qds[f"qd_y_{i0}"]) +
                                qds[f"qd_x_{i2}"] * (qds[f"qd_y_{i0}"] - qds[f"qd_y_{i1}"]))
                circle_x = np.divide(qds[f"qd_r_{i0}"]**2 * (qds[f"qd_y_{i1}"] - qds[f"qd_y_{i2}"]) +
                                     qds[f"qd_r_{i1}"]**2 * (qds[f"qd_y_{i2}"] - qds[f"qd_y_{i0}"]) +
                                     qds[f"qd_r_{i2}"]**2 * (qds[f"qd_y_{i0}"] - qds[f"qd_y_{i1}"]),
                                     circle_d)
                circle_y = np.divide(qds[f"qd_r_{i0}"]**2 * (qds[f"qd_x_{i2}"] - qds[f"qd_x_{i1}"]) +
                                     qds[f"qd_r_{i1}"]**2 * (qds[f"qd_x_{i0}"] - qds[f"qd_x_{i2}"]) +
                                     qds[f"qd_r_{i2}"]**2 * (qds[f"qd_x_{i1}"] - qds[f"qd_x_{i0}"]),
                                     circle_d)
                circle_r = np.sqrt((qds[f"qd_x_{i0}"] - circle_x)**2 + (qds[f"qd_y_{i0}"] - circle_y)**2)
                circle_ok = circle_d != 0
                if np.any(~circle_ok):
                    logger.warning(f"Found {np.sum(~circle_ok)} invalid circles with circle_d = 0")
                for ix in ixs:
                    circle_diff = np.sqrt((qds[f"qd_x_{ix}"] - circle_x)**2 + (qds[f"qd_y_{ix}"] - circle_y)**2) - circle_r
                    qds[f"qd_chi2_{i0}{i1}{i2}_vs_{ix}"] = np.where(circle_ok, np.abs(circle_diff), BAD_CHI2)

                # calculate the average diff
                chi2cols = [f"qd_chi2_{i0}{i1}{i2}_vs_{ix}" for ix in ixs]
                qds[f"qd_chi2_{i0}{i1}{i2}"] = qds[chi2cols].mean(axis=1)

                # rename some things
                rename = {
                    "ls_system": "qd_system",
                    "ls_doublelayer_lower": "qd_doublelayer_lower",
                    "ls_doublelayer_upper": "qd_doublelayer_upper",
                    "ls_module_lower": "qd_module_lower",
                    "ls_module_upper": "qd_module_upper",
                    "ls_sensor_lower": "qd_sensor_lower",
                    "ls_sensor_upper": "qd_sensor_upper",
                    "ls_dr_lower": "qd_dr_lower",
                    "ls_dr_upper": "qd_dr_upper",
                    "ls_dz_lower": "qd_dz_lower",
                    "ls_dz_upper": "qd_dz_upper",
                }
                qds = qds.rename(columns=rename)

                # drop other cols
                dropcols = ["i_mcp_lower", "i_mcp_upper"]
                dropcols.extend([col for col in qds.columns if col.startswith("simhit_")])
                dropcols.extend([col for col in qds.columns if col.startswith("doublet_")])
                dropcols.extend([col for col in qds.columns if col.startswith("ls_")])
                dropcols.extend([col for col in qds.columns if col.startswith("mcp_") and col.endswith("_lower")])
                dropcols.extend([col for col in qds.columns if col.startswith("mcp_") and col.endswith("_upper")])
                qds.drop(columns=dropcols, errors="ignore", inplace=True)

                # tmp
                file, system, dldiv2, dleven = cols
                if file == 1 and dldiv2 == 0:
                    print(qds.columns)
                    print(qds[ ["file", "i_event", "i_mcp", "qd_system", "qd_module_lower", "qd_module_upper", f"qd_chi2_{i0}{i1}{i2}"] ])
                    print("*"*20)
