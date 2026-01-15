import numpy as np
import pandas as pd
import time

class DoubletMaker:


    def __init__(self, simhits: pd.DataFrame):
        self.df = self.make_doublets(simhits)


    def make_doublets(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Making doublets ...")
        doublelayer_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
        ]
        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_module", # the phi-module
            "simhit_sensor", # the z-sensor
        ]
        doublets_list = []
        # groups = df.groupby(doublet_cols)
        groups = df.groupby(doublelayer_cols)
        for i_group, (cols, group) in enumerate(groups):

            if len(group) < 3:
                continue
            # if i_group > 10:
            #     break
            if i_group % 1000 == 0:
                print(f"Processing group {i_group+1}/{len(groups)} at {time.strftime('%Y-%m-%d %H:%M:%S')}...")

            lower_cols = doublet_cols + [
                "i_mcp_lower",
                "simhit_r_lower",
                "simhit_z_lower",
                "simhit_x_lower",
                "simhit_y_lower"
                ]
            upper_cols = doublet_cols + [
                "i_mcp_upper",
                "simhit_r_upper",
                "simhit_z_upper",
                "simhit_x_upper",
                "simhit_y_upper"
                ]
            lower_mask = group["simhit_layer_mod_2"] == 0
            upper_mask = group["simhit_layer_mod_2"] == 1

            # print("Getting lower and upper hits ...")
            lower = (group[lower_mask].rename(columns={
                "i_mcp":"i_mcp_lower",
                "simhit_r":"simhit_r_lower",
                "simhit_z":"simhit_z_lower",
                "simhit_x":"simhit_x_lower",
                "simhit_y":"simhit_y_lower",
            })[lower_cols])
            upper = (group[upper_mask].rename(columns={
                "i_mcp":"i_mcp_upper",
                "simhit_r":"simhit_r_upper",
                "simhit_z":"simhit_z_upper",
                "simhit_x":"simhit_x_upper",
                "simhit_y":"simhit_y_upper",
            })[upper_cols])

            # inner join to find doublets
            # print("Joining ...")
            doublets = lower.merge(upper, on=doublet_cols, how="inner")

            # rz
            slope = np.divide(doublets["simhit_z_upper"] - doublets["simhit_z_lower"],
                              doublets["simhit_r_upper"] - doublets["simhit_r_lower"])
            doublets["intercept_rz"] = doublets["simhit_z_lower"] - doublets["simhit_r_lower"] * slope

            # xy
            phi_local = np.arctan2(doublets["simhit_y_upper"] - doublets["simhit_y_lower"],
                                   doublets["simhit_x_upper"] - doublets["simhit_x_lower"])
            phi_global = np.arctan2((doublets["simhit_y_lower"] + doublets["simhit_y_upper"]) / 2.0,
                                    (doublets["simhit_x_lower"] + doublets["simhit_x_upper"]) / 2.0)
            doublets["dphi"] = phi_local - phi_global
            doublets["dphi"] = (doublets["dphi"] + np.pi) % (2 * np.pi) - np.pi

            # apply cuts
            condition_rz = np.abs(doublets["intercept_rz"]) < 50 # mm
            condition_xy = np.abs(doublets["dphi"]) < 0.55 # rad
            condition = condition_rz & condition_xy

            # print
            # print(f"Found {len(lower)} lower hits")
            # print(f"Found {len(upper)} upper hits")
            # print(f"Found {len(doublets)} doublets total in group {i_group+1}/{len(groups)}")
            # print(f" rz cut: {np.sum(condition_rz)} aka {np.sum(condition_rz) / len(doublets)} efficiency")
            # print(f" xy cut: {np.sum(condition_xy)} aka {np.sum(condition_xy) / len(doublets)} efficiency")
            # print(f" rz & xy: {np.sum(condition)} aka {np.sum(condition) / len(doublets)} efficiency")
            # doublets = doublets[condition]

            # if len(doublets) > 0:
            #     print(f"Doublets found in event {cols[1]}: system {cols[2]}, layer {cols[3]}, module {cols[4]}, sensor {cols[5]}")
            #     print(group[doublet_cols + ["simhit_layer", "simhit_x", "simhit_y", "simhit_z"]])
            #     print("Doublets:")
            #     print(doublets)
            #     print("->", len(doublets[np.abs(doublets["intercept_rz"]) < 50]))
            #     print("*"*100)
            # else:
            #     print(f"No doublets found in event {cols[1]}: system {cols[2]}, layer {cols[3]}, module {cols[4]}, sensor {cols[5]}")
            doublets_list.append(doublets)


        if len(doublets_list) == 0:
            raise ValueError("No doublets found in the DataFrame")

        return pd.concat(doublets_list, ignore_index=True)
