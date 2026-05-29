"""
This module defines the T4Maker class, which creates a T4 from two T2s.
All T2s in layers 0-3 are considered for combination with T2s in layers 4-7.
The T2s are combined if they satisfy goodness criteria.
To avoid filling the memory with all possible combinations, combination is done with a groupby approach.

"""

import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from constants import BYTE_TO_MB, NO_MCP

class T4Maker:

    def __init__(self, geometry_version: str, sim: bool, smear: str, t2s: pd.DataFrame, signal: bool, cut_t4s: bool):
        self.df = None
        self.signal = signal
        self.cut_t4s = cut_t4s
        self.t2s = t2s.copy()
        memory = self.t2s.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Making T4s. T2 dataframe size: {memory:.2f} MB")
        key = (geometry_version, "sim") if sim else (geometry_version, "digi", smear)
        self.prep_t2s()
        self.make_t4s()


    def prep_t2s(self) -> None:
        logger.info("Preprocessing T2s for T4 making ...")


    def make_t4s(self) -> None:
        logger.info("Making T4s ...")

        # one loop for now:
        # layers 0123 combined with layers 4567
        # equivalently, doublelayers 01 combined with 23 (doublelayer // 4 == 0)

        groupby_cols = [
            "file",
            "ls_system",
            "ls_doublelayer_div_4",
            "ls_doublelayer_even",
        ]
        n_group = len(self.t2s.groupby(groupby_cols))

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

        for i_group, (cols, df) in enumerate(self.t2s.groupby(groupby_cols)):
            logger.info(f"Processing group {i_group} / {n_group} for T4s (n={len(df)}) ...")
            if len(df) == 0:
                continue
            logger.info(cols)

            lower = df[df["ls_doublelayer_mod_4"] == 0]
            upper = df[df["ls_doublelayer_mod_4"] == 2]
            logger.info(f"Lower: {len(lower)}, Upper: {len(upper)}")

            for i_subgroup, (subcols, subdf) in enumerate(df.groupby(subgroup_cols)):

                upper = subdf[ subdf["ls_doublelayer_mod_4"] > 0 ]

                # get all combinations of lower and upper
                t4s = lower.merge(
                    upper,
                    on=merge_keys,
                    how="inner",
                    validate="many_to_many",
                    suffixes=("_lower", "_upper"),
                )
                logger.info(f"Lower: {len(lower)}, Upper: {len(upper)}, Combos: {len(t4s)}")

                # the doublelayer
                t4s["t4_doublelayer"] = t4s["ls_doublelayer_lower"]

                # rz projection
                slope_rz = np.divide(t4s["ls_z_upper"] - t4s["ls_z_lower"],
                                     t4s["ls_r_upper"] - t4s["ls_r_lower"])
                t4s["ls_z"] = t4s["ls_z_lower"] - t4s["ls_r_lower"] * slope_rz

                # xy projection
                slope_xy = np.divide(t4s["ls_y_upper"] - t4s["ls_y_lower"],
                                     t4s["ls_x_upper"] - t4s["ls_x_lower"])
                intercept_xy = t4s["ls_y_lower"] - t4s["ls_x_lower"] * slope_xy
                t4s["t4_dr"] = np.abs(intercept_xy) / np.sqrt(1 + slope_xy**2)

                # assign truth info
                mcp_ok = t4s["i_mcp_lower"] == t4s["i_mcp_upper"]
                t4s["i_mcp"] = t4s["i_mcp_lower"].where(mcp_ok, NO_MCP)
                if self.signal:
                    t4s["t4_first_exit"] = t4s["ls_first_exit_lower"] & t4s["ls_first_exit_upper"]
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
                        t4s[attr] = t4s[f"{attr}_lower"].where(mcp_ok, 0)

                # pass-through the simhit positions
                for coord in ["x", "y", "r"]:
                    t4s[f"t4_{coord}_0"] = t4s[f"ls_{coord}_0_lower"]
                    t4s[f"t4_{coord}_1"] = t4s[f"ls_{coord}_1_lower"]
                    t4s[f"t4_{coord}_2"] = t4s[f"ls_{coord}_2_lower"]
                    t4s[f"t4_{coord}_3"] = t4s[f"ls_{coord}_3_lower"]
                    t4s[f"t4_{coord}_4"] = t4s[f"ls_{coord}_0_upper"]
                    t4s[f"t4_{coord}_5"] = t4s[f"ls_{coord}_1_upper"]
                    t4s[f"t4_{coord}_6"] = t4s[f"ls_{coord}_2_upper"]
                    t4s[f"t4_{coord}_7"] = t4s[f"ls_{coord}_3_upper"]

                # find the circle (radius, x_center, y_center) formed from the first three hits
                BAD_CHI2 = 1e6
                i0, i1, i2 = 0, 4, 7
                ixs = [1, 2, 3, 5, 6]
                circle_d = 2 * (t4s[f"t4_x_{i0}"] * (t4s[f"t4_y_{i1}"] - t4s[f"t4_y_{i2}"]) +
                                t4s[f"t4_x_{i1}"] * (t4s[f"t4_y_{i2}"] - t4s[f"t4_y_{i0}"]) +
                                t4s[f"t4_x_{i2}"] * (t4s[f"t4_y_{i0}"] - t4s[f"t4_y_{i1}"]))
                circle_x = np.divide(t4s[f"t4_r_{i0}"]**2 * (t4s[f"t4_y_{i1}"] - t4s[f"t4_y_{i2}"]) +
                                     t4s[f"t4_r_{i1}"]**2 * (t4s[f"t4_y_{i2}"] - t4s[f"t4_y_{i0}"]) +
                                     t4s[f"t4_r_{i2}"]**2 * (t4s[f"t4_y_{i0}"] - t4s[f"t4_y_{i1}"]),
                                     circle_d)
                circle_y = np.divide(t4s[f"t4_r_{i0}"]**2 * (t4s[f"t4_x_{i2}"] - t4s[f"t4_x_{i1}"]) +
                                     t4s[f"t4_r_{i1}"]**2 * (t4s[f"t4_x_{i0}"] - t4s[f"t4_x_{i2}"]) +
                                     t4s[f"t4_r_{i2}"]**2 * (t4s[f"t4_x_{i1}"] - t4s[f"t4_x_{i0}"]),
                                     circle_d)
                circle_r = np.sqrt((t4s[f"t4_x_{i0}"] - circle_x)**2 + (t4s[f"t4_y_{i0}"] - circle_y)**2)
                circle_ok = circle_d != 0
                if np.any(~circle_ok):
                    logger.warning(f"Found {np.sum(~circle_ok)} invalid circles with circle_d = 0")
                for ix in ixs:
                    circle_diff = np.sqrt((t4s[f"t4_x_{ix}"] - circle_x)**2 + (t4s[f"t4_y_{ix}"] - circle_y)**2) - circle_r
                    t4s[f"t4_chi2_{i0}{i1}{i2}_vs_{ix}"] = np.where(circle_ok, np.abs(circle_diff), BAD_CHI2)

                # calculate the average diff
                chi2cols = [f"t4_chi2_{i0}{i1}{i2}_vs_{ix}" for ix in ixs]
                t4s[f"t4_chi2_{i0}{i1}{i2}"] = t4s[chi2cols].mean(axis=1)

                # rename some things
                rename = {
                    "ls_system": "t4_system",
                    "ls_doublelayer_lower": "t4_doublelayer_lower",
                    "ls_doublelayer_upper": "t4_doublelayer_upper",
                    "ls_module_lower": "t4_module_lower",
                    "ls_module_upper": "t4_module_upper",
                    "ls_sensor_lower": "t4_sensor_lower",
                    "ls_sensor_upper": "t4_sensor_upper",
                    "ls_dr_lower": "t4_dr_lower",
                    "ls_dr_upper": "t4_dr_upper",
                    "ls_dz_lower": "t4_dz_lower",
                    "ls_dz_upper": "t4_dz_upper",
                }
                t4s = t4s.rename(columns=rename)

                # drop other cols
                dropcols = ["i_mcp_lower", "i_mcp_upper"]
                dropcols.extend([col for col in t4s.columns if col.startswith("simhit_")])
                dropcols.extend([col for col in t4s.columns if col.startswith("doublet_")])
                dropcols.extend([col for col in t4s.columns if col.startswith("ls_")])
                dropcols.extend([col for col in t4s.columns if col.startswith("mcp_") and col.endswith("_lower")])
                dropcols.extend([col for col in t4s.columns if col.startswith("mcp_") and col.endswith("_upper")])
                t4s.drop(columns=dropcols, errors="ignore", inplace=True)

                # tmp
                file, system, dldiv2, dleven = cols
                if self.signal and file == 1 and dldiv2 == 0:
                    print(t4s.columns)
                    print(t4s[ ["file", "i_event", "i_mcp", "t4_system", "t4_module_lower", "t4_module_upper", f"t4_chi2_{i0}{i1}{i2}"] ])
                    print("*"*20)
