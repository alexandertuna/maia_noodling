import numpy as np
import pandas as pd
from constants import MINIMUM_PT


class HitsToModuleMap:


    def __init__(self, sorted_hits_df: pd.DataFrame):
        self.sorted_hits_df = sorted_hits_df


    def make_module_map(self):
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
        with pd.option_context("display.min_rows", 20,
                               "display.max_rows", 20,
                               ):
            print(self.group_df)

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

