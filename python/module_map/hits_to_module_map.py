import numpy as np
import pandas as pd
from constants import MINIMUM_FRACTION_PER_MODULE, MINIMUM_HITS_PER_MODULE


class HitsToModuleMap:


    def __init__(self, barrel_only: bool, sorted_hits_df: pd.DataFrame):
        self.barrel_only = barrel_only
        self.sorted_hits_df = sorted_hits_df


    def make_module_map(self):
        # self.remove_innermost_doublet_layers()
        self.merge_rows()
        return self.group_df


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

        print("Finding the fraction of repeated rows ...")
        cols = ["hit_system", "hit_side", "hit_layer", "hit_module", "hit_sensor"]
        self.group_df["fraction"] = self.group_df["count"] / self.group_df.groupby(cols)["count"].transform("sum")

        with pd.option_context("display.min_rows", 20,
                               "display.max_rows", 20,
                               ):
            print(self.group_df)

        print("")
        print(f"Maximum number of counts: {self.group_df['count'].max()}")
        print("")
        # self.group_df = self.group_df[self.group_df['count'] >= MINIMUM_HITS_PER_MODULE]
        self.group_df = self.group_df[self.group_df['fraction'] >= MINIMUM_FRACTION_PER_MODULE]

        parents = self.group_df[[
            "hit_system",
            "hit_side",
            "hit_layer",
            "hit_module",
            "hit_sensor",
        ]]
        print("Parents:")
        print(parents)
        print("Unique Parents:")
        print(parents.drop_duplicates())

