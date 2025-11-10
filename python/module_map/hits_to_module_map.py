import numpy as np
import pandas as pd
from constants import MINIMUM_PT


class HitsToModuleMap:


    def __init__(self, hits_df: pd.DataFrame):
        self.hits_df = hits_df


    def make_module_map(self):
        self.get_next_row()
        self.filter_valid_rows()
        self.drop_non_module_columns()
        self.sort_rows()
        self.merge_rows()
        # return self.module_df
        return self.group_df


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


    def drop_non_module_columns(self):
        print("Dropping hit columns ...")
        columns = [
                "file",
                "i_event",
                "i_sim",
                "next_i_event",
                "next_i_sim",
                "hit_x",
                "hit_y",
                "hit_z",
                "hit_r",
                "hit_R",
                # "hit_sensor",
                "sim_p",
                "sim_pt",
                "sim_px",
                "sim_py",
                "sim_pz",
                "sim_eta",
                "sim_phi",
                "sim_m",
                "sim_q",
        ]
        columns = [col for col in columns if col in self.hits_df.columns]
        #################### self.module_df = self.hits_df[self.valid].drop(columns=columns) ####### PUT ME BACK
        self.module_df = self.hits_df[self.valid] # PUT HIM BACK TODO TUNA
        print(self.module_df)


    def sort_rows(self):
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
        self.module_df = self.module_df.sort_values(by=columns)
        print(self.module_df)

        """
            hit_layer  hit_module  hit_side  hit_system  next_hit_system  next_hit_side  next_hit_layer  next_hit_module  count
        0              0           0         0           3                3              0               0                0    174
        1              0           0         0           3                3              0               0                1     88
        2              0           0         0           3                3              0               0               29    106
        3              0           0         0           3                3              0               1                0  10601
        4              0           0         0           3                3              0               2                0     36
        """

        print("Counting repeated rows ...")
        self.group_df = self.module_df

        
        test_group_df = self.module_df.groupby(list(self.module_df.columns)).size().reset_index(name="count")
        with pd.option_context("display.min_rows", 20,
                               "display.max_rows", 20,
                               ):
            print(test_group_df)

        parents = self.module_df[[
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


    def merge_rows(self):
        pass

