import numpy as np
import pandas as pd
from constants import MINIMUM_PT


class GetNextHitAndSort:


    def __init__(self,
                 barrel_only: bool,
                 hits_df: pd.DataFrame,
                 ):
        self.barrel_only = barrel_only
        self.hits_df = hits_df


    def get_next_hit_and_sort_by_module(self):
        self.get_next_row()
        self.filter_valid_rows()
        self.sort_rows_by_module()
        return self.sorted_df


    def get_next_row(self):
        print("Getting next row ...")
        for col in [
            "i_event",
            "i_sim",
            "hit_system",
            "hit_side",
            "hit_layer",
            "hit_module",
            "hit_sensor",
            "hit_x",
            "hit_y",
            "hit_z",
            "hit_r",
            "hit_theta",
            "hit_phi",
            ]:
            self.hits_df[f"next_{col}"] = self.hits_df[col].shift(-1).fillna(-1).astype(self.hits_df[col].dtype)
        print(self.hits_df)


    def filter_valid_rows(self):
        print("Filtering valid rows ...")
        if not self.barrel_only:
            raise ValueError("filter_valid_rows is only implemented for barrel-only dataframes.")
        self.valid = (
            (self.hits_df["sim_pt"] > MINIMUM_PT) &
            (self.hits_df["i_event"] == self.hits_df["next_i_event"]) &
            (self.hits_df["i_sim"] == self.hits_df["next_i_sim"]) &

            # barrel-only specific:
            (self.hits_df["hit_layer"] % 2 == 1) &
            (self.hits_df["next_hit_layer"] == self.hits_df["hit_layer"] + 1)
        )
        print(self.hits_df[self.valid])
        self.hits_df = self.hits_df[self.valid]


    def sort_rows_by_module(self):
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
        self.sorted_df = self.hits_df.sort_values(by=columns)
        print(self.sorted_df)

