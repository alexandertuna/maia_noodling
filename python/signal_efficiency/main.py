import pandas as pd
from slcio_to_hits import SlcioToHitsDataFrame

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})


FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_sim_100.slcio"
# FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_12_11_00h00m00s/muonGun_pT_0_10_sim_0.slcio"
COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]

def main():
    df = SlcioToHitsDataFrame(
        slcio_file_paths=[FNAME],
        collections=COLLECTIONS,
    ).convert()

    # show the dataframe
    with pd.option_context("display.min_rows", 50,
                           "display.max_rows", 50,
                          ):
        print(df)
    mask = df["hit"]
    mask_inside = (mask & df["hit_inside_bounds"])
    print("Number of hits:", mask.sum())
    print("Number of hits inside bounds:", mask_inside.sum())

    # make some event displays
    with PdfPages("event_displays.pdf") as pdf:
        group_cols = ["file", "i_event"]
        for (file, i_event), group in df.groupby(group_cols):
            if i_event >= 30:
                break
            fig, ax = plt.subplots(figsize=(8,8))
            dr_inner = 1
            dr_outer = 6
            radii = [127 + dr_inner,
                     167 + dr_inner,
                     510 + dr_inner,
                     550 + dr_inner,
                     819 + dr_outer,
                     899 + dr_outer,
                     1366 + dr_outer,
                     1446 + dr_outer,
                     ]
            for r in radii:
                circle = plt.Circle((0,0), r, color="gray", fill=False, linestyle="-", alpha=0.5)
                ax.add_artist(circle)
            sim = group[group["hit"]]
            ax.scatter(
                sim["hit_x"],
                sim["hit_y"],
                c="blue",
                s=20,
                label="sim hits",
                alpha=0.7,
            )
            ax.set_title(f"Event display for event {i_event}")
            ax.set_xlabel("x [mm]")
            ax.set_ylabel("y [mm]")
            ax.set_xlim(-1490, 1490)
            ax.set_ylim(-1490, 1490)
            ax.grid()            
            ax.tick_params(which="both", direction="in", top=True, right=True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            plt.close()



    # print some info about out-of-bounds hits
    i_outside = 0
    group_cols = ["file", "i_event", "i_sim"]
    for (file, i_event, i_sim), group in df.groupby(group_cols):
        outside = (group["hit"] & ~group["hit_inside_bounds"])
        if not outside.any():
            continue
        mask = group["hit"]
        cols = ["i_event",
                "i_sim",
                "sim_pt",
                "sim_eta",
                "sim_phi",
                "sim_pdg",
                "hit_inside_bounds",
                "hit_distance",
                "hit_pathlength",
                "hit_system",
                "hit_layer",
                "hit_module",
                "hit_sensor",
                "hit_eta",
                "hit_phi",
                ]
        print("-"*30)
        with pd.option_context("display.min_rows", 50,
                               "display.max_rows", 50,
                               "display.max_columns", None,
                               "display.width", None,
                               "display.max_colwidth", None,
                            ):
            print(group[mask][cols])
        i_outside += 1
        if i_outside >= 50:
            break



if __name__ == "__main__":
    main()
