import numpy as np
import pandas as pd
from constants import MINIMUM_PT


class GetNextHitAndSort:


    def __init__(self, hits_df: pd.DataFrame):
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
            ]:
            self.hits_df[f"next_{col}"] = self.hits_df[col].shift(-1).fillna(-1).astype(self.hits_df[col].dtype)
        print(self.hits_df)


    def filter_valid_rows(self):
        print("Filtering valid rows ...")
        self.valid = (
            (self.hits_df["i_event"] == self.hits_df["next_i_event"]) &
            (self.hits_df["i_sim"] == self.hits_df["next_i_sim"]) &
            (self.hits_df["sim_pt"] > MINIMUM_PT)
        )
        print(self.hits_df[self.valid])



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
        self.sorted_df = self.hits_df[self.valid].sort_values(by=columns)
        print(self.sorted_df)

