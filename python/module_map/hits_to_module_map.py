import numpy as np
import pandas as pd
from constants import MINIMUM_PT, MINIMUM_HITS_PER_MODULE


class HitsToModuleMap:


    def __init__(self, barrel_only: bool, sorted_hits_df: pd.DataFrame):
        self.barrel_only = barrel_only
        self.sorted_hits_df = sorted_hits_df


    def make_module_map(self):
        self.remove_innermost_doublet_layers()
        self.merge_rows()
        return self.group_df


    def remove_innermost_doublet_layers(self):
        """
        The module mapping is for minidoublet-minidoublet mapping.
        Therefore, we need to ignore hits in the innermost layers of a minidoublet,
        and we only consider next hits in the subsequent layer.
        e.g., if we have hits in layers 0, 1, 2, 3, then
        we only want to consider the connection between layers 1 and 2.
        """
        if not self.barrel_only:
            raise ValueError("Removing innermost doublet layers is only implemented for barrel-only dataframes.")
        mask = (
            (self.sorted_hits_df["hit_layer"] % 2 == 1) &
            (self.sorted_hits_df["next_hit_layer"] == self.sorted_hits_df["hit_layer"] + 1)
        )
        self.sorted_hits_df = self.sorted_hits_df[mask]


    def merge_rows(self):
        print("Sorting rows ...")
        columns = [
            "hit_system",
            "hit_side",
            "hit_layer",
            "hit_module",
            "hit_sensor",
            "next_hit_system",
            "next_hit_side",
            "next_hit_layer",
            "next_hit_module",
            "next_hit_sensor",
        ]

        print("Counting repeated rows ...")
        self.group_df = self.sorted_hits_df.groupby(columns).size().reset_index(name="count")
        with pd.option_context("display.min_rows", 20,
                               "display.max_rows", 20,
                               ):
            print(self.group_df)

        print("")
        print(f"Maximum number of counts: {self.group_df['count'].max()}")
        print("")
        self.group_df = self.group_df[self.group_df['count'] >= MINIMUM_HITS_PER_MODULE]

        # parents = self.sorted_hits_df[[
        #     "hit_system",
        #     "hit_side",
        #     "hit_layer",
        #     "hit_module",
        #     "hit_sensor",
        # ]]
        # print("Parents:")
        # print(parents)
        # print("Unique Parents:")
        # print(parents.drop_duplicates())

