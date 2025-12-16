import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

PARQUET = "geometry.parquet"
NEARBY = 30 # mm
NEARBY2 = NEARBY**2
PADDING = 50 # mm
MAX_TIME_CORRECTED = 3.0 # ns
MIN_HITS_FOR_CIRCLE = 3
TOTAL_LAYERS = 16

INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5
TRACKERS = [INNER_TRACKER_BARREL, OUTER_TRACKER_BARREL]
TRACKERNAME = {
    INNER_TRACKER_BARREL: "Inner Tracker",
    OUTER_TRACKER_BARREL: "Outer Tracker",
}


class EventDisplays:


    def __init__(self, df, pdf):
        self.df = df
        self.pdf = pdf
        self.geo = pd.read_parquet(PARQUET)
        self.geo["origin_r"] = np.sqrt(self.geo["origin_x"]**2 + self.geo["origin_y"]**2)
        self.geo["origin_phi"] = np.arctan2(self.geo["origin_y"], self.geo["origin_x"])


    def make_event_displays(self):
        with PdfPages(self.pdf) as pdf:
            group_cols = ["file", "i_event", "i_mcp"]
            for i_group, (cols, group) in enumerate(self.df.groupby(group_cols)):
                if i_group >= 100:
                    break
                self.make_one_event_display(i_group, group, pdf)


    def make_one_event_display(self, i_group, group, pdf):
        mask = group["simhit"] & (group["simhit_t_corrected"] < MAX_TIME_CORRECTED)
        if mask.sum() < MIN_HITS_FOR_CIRCLE:
            raise ValueError("Not enough simhits to make an event display.")

        # check if any layers are missing
        cols = ["simhit_system", "simhit_layer"]
        n_layers = len(group[cols].drop_duplicates())
        if n_layers < TOTAL_LAYERS:
            print(f"Event display mcparticle {i_group}: WARNING! Only {n_layers} layers have hits.")

        # get x, y for convenience
        group["simhit_x"] = group["simhit_r"] * np.cos(group["simhit_phi"])
        group["simhit_y"] = group["simhit_r"] * np.sin(group["simhit_phi"])

        # fit a circle
        x_center, y_center, radius = fit_circle(group[mask]["simhit_x"],
                                                group[mask]["simhit_y"])
        thetas = np.linspace(0, 2*np.pi, 360)
        circle_x = x_center + radius * np.cos(thetas)
        circle_y = y_center + radius * np.sin(thetas)

        # find nearby modules
        hits = group[mask][["simhit_x", "simhit_y", "simhit_z"]].to_numpy(dtype=np.float64)
        orig = self.geo[["origin_x", "origin_y", "origin_z"]].to_numpy(dtype=np.float64)
        d2 = ((hits[:, None, :] - orig[None, :, :]) ** 2).sum(axis=2)
        min_d2 = d2.min(axis=0)
        geomask = min_d2 <= NEARBY2
        print(f"Event display mcparticle {i_group}: found {geomask.sum()} nearby modules.")

        # one plot for IT and one plot for OT
        for tracker in TRACKERS:

            trackermask = mask & (group["simhit_system"] == tracker)

            fig, ax = plt.subplots(figsize=(8, 8))
            for _, row in self.geo[geomask].iterrows():
                corner_xs = [row["corner_xy_0_x"],
                             row["corner_xy_1_x"],
                             row["corner_xy_2_x"],
                             row["corner_xy_3_x"],
                             row["corner_xy_0_x"]
                            ]
                corner_ys = [row["corner_xy_0_y"],
                             row["corner_xy_1_y"],
                             row["corner_xy_2_y"],
                             row["corner_xy_3_y"],
                             row["corner_xy_0_y"]
                            ]
                ax.plot(corner_xs, corner_ys, c="green", marker="none", linewidth=0.5, zorder=1)
            ax.plot(
                circle_x,
                circle_y,
                c="red",
                linestyle="--",
                linewidth=0.5,
                zorder=2,
            )
            mask_even = trackermask & (group["simhit_layer"] % 2 == 0)
            mask_odd = trackermask & (group["simhit_layer"] % 2 == 1)
            ops = dict(facecolors="none", edgecolors="dodgerblue", s=20, zorder=3)
            ax.scatter(
                group[mask_even]["simhit_x"],
                group[mask_even]["simhit_y"],
                marker="o",
                **ops,
            )
            ax.scatter(
                group[mask_odd]["simhit_x"],
                group[mask_odd]["simhit_y"],
                marker="s",
                **ops,
            )

            ax.set_xlim([group[trackermask]["simhit_x"].min() - PADDING,
                         group[trackermask]["simhit_x"].max() + PADDING])
            ax.set_ylim([group[trackermask]["simhit_y"].min() - PADDING,
                         group[trackermask]["simhit_y"].max() + PADDING])
            ax.set_xlabel("x [mm]")
            ax.set_ylabel("y [mm]")
            ax.set_title(f"{TRACKERNAME[tracker]} display, mcparticle {i_group}")
            ax.minorticks_on()
            ax.grid(which="both", alpha=0.5)
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
            pdf.savefig()
            plt.close()


def fit_circle(
        x,
        y,
    ):
    """
    Fit a circle in the least-squares sense to points (x, y).

    Returns:
        xc, yc, R  (center and radius)
    """
    x = np.asarray(x)
    y = np.asarray(y)

    # Build the system: [x y 1] [D E F]^T = -(x^2 + y^2)
    A = np.column_stack([x, y, np.ones_like(x)])
    b = -(x**2 + y**2)

    D, E, F = np.linalg.lstsq(A, b, rcond=None)[0]

    xc = -D / 2.0
    yc = -E / 2.0
    R = np.sqrt((D**2 + E**2) / 4.0 - F)

    return xc, yc, R