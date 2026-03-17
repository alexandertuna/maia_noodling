import pandas as pd
import logging
logger = logging.getLogger(__name__)

from constants import DZ_CUT, DR_CUT
from constants import BYTE_TO_MB

class ModuleMap:
    def __init__(self, doublets: pd.DataFrame):
        memory = doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Making modulemap with doublets memory {memory:.1f} MB ...")
        self.doublets = doublets.copy()
        self.remove_columns_from_doublets()
        self.filter_doublets()
        self.sort_doublets()
        self.make_quadruplets()
        self.check_quadruplets()
        self.simplify_quadruplet_columns()
        self.make_modulemap()
        self.print_modulemap_test(sensor=20, module=0)


    def remove_columns_from_doublets(self):
        cols = [
            "simhit_x_lower",
            "simhit_x_upper",
            "simhit_y_lower",
            "simhit_y_upper",
            "simhit_z_lower",
            "simhit_z_upper",
            "simhit_p_lower",
            "simhit_p_upper",
            "simhit_costheta_lower",
            "simhit_costheta_upper",
            "simhit_t_corrected_lower",
            "simhit_t_corrected_upper",
        ]
        self.doublets = self.doublets.drop(columns=cols)
        memory = self.doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage after removing columns: {memory:.1f} MB")


    def filter_doublets(self):
        # only consider "good" doublets
        logger.info("Filtering doublets for modulemap ...")
        doublelayer = self.doublets["simhit_layer_div_2"]
        self.doublets = self.doublets[
            (self.doublets["i_mcp_lower"] == self.doublets["i_mcp_upper"]) &
            (self.doublets["doublet_dz"] < DZ_CUT[doublelayer]) &
            (self.doublets["doublet_dr"] < DR_CUT[doublelayer])
        ]
        self.doublets = self.doublets.rename(columns={"i_mcp_lower": "i_mcp"}).drop(columns=["i_mcp_upper"])
        memory = self.doublets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage after filtering doublets: {memory:.1f} MB")


    def sort_doublets(self):
        # sort doublets by file, event, mcp, system, doublelayer, and r for better intuition
        logger.info("Sorting doublets for modulemap ...")
        cols = [
            "file",
            "i_event",
            "i_mcp",
            "simhit_system",
            "simhit_layer_div_2",
            "simhit_r_lower",
        ]
        self.doublets = self.doublets.sort_values(by=cols).reset_index(drop=True)


    def make_quadruplets(self):
        # modulemap = {}

        groupby_cols = [
            "file",
        ]

        keys = [
            "file",
            "i_event",
            "i_mcp",
        ]

        quadruplets = []

        for group, df in self.doublets.groupby(groupby_cols):

            for system in [5]: # old approach: hard-coded systems

                mask_system = df["simhit_system"] == system

                for doublelayer in [0, 1]: # old approach: hard-coded doublelayers

                    if doublelayer % 2 != 0:
                        continue

                    mask_lower = mask_system & (df["simhit_layer_div_2"] == doublelayer)
                    mask_upper = mask_system & (df["simhit_layer_div_2"] == doublelayer + 1)

                    lower = df[mask_lower]
                    upper = df[mask_upper]
                    quads = lower.merge(
                        upper,
                        on=keys,
                        how="inner",
                        validate="many_to_many",
                        suffixes=("_lower", "_upper"),
                    )
                    quadruplets.append(quads)

        self.quadruplets = pd.concat(quadruplets, ignore_index=True)


    def check_quadruplets(self):
        logger.info("Checking quadruplets for modulemap ...")

        # checks
        for i_check, check in enumerate([
            self.quadruplets["simhit_system_lower"] == self.quadruplets["simhit_system_upper"],
            self.quadruplets["simhit_layer_div_2_lower"] == self.quadruplets["simhit_layer_div_2_upper"] - 1,
        ]):
            if not check.all():
                raise ValueError(f"Check {i_check} failed for quadruplets in modulemap")


    def simplify_quadruplet_columns(self):
        logger.info("Simplifying quadruplet columns for modulemap ...")
        rename = {
            "simhit_system_lower": "simhit_system",
        }
        drop = [
            "simhit_system_upper",
        ]
        self.quadruplets = self.quadruplets.rename(columns=rename).drop(columns=drop)
        memory = self.quadruplets.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Memory usage after simplifying quadruplet columns: {memory:.1f} MB")


    def make_modulemap(self):
        logger.info("Making modulemap ...")
        mapcols = [
            "simhit_system",
            "simhit_layer_div_2_lower",
            "simhit_layer_div_2_upper",
            "simhit_module_lower",
            "simhit_sensor_lower",
            "simhit_module_upper",
            "simhit_sensor_upper"
        ]
        self.modulemap = self.quadruplets.groupby(mapcols).size().reset_index(name="number")


    def print_modulemap_test(self, sensor: int, module: int):
        logger.info(f"Testing modulemap for sensor {sensor} and module {module} ...")
        test = self.modulemap[
            (self.modulemap["simhit_sensor_lower"] == sensor) &
            (self.modulemap["simhit_module_lower"] == module)
        ]
        with pd.option_context("display.min_rows", 50,
                               "display.max_rows", 50,
                               ):
            logger.info(f"Modulemap test for sensor {sensor} and module {module}:")
            logger.info(f"\n{test.to_string(index=False)}")

