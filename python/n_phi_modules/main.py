"""
A quick study of how to stagger modules in phi to get hermetic-ish coverage.
This assumes modules are staggered like -_-_-_- in phi.
A configuration can then be described by:
- nphi
- inner radius
- outer radius
- module width (mm)
Module thickness isnt considered.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({
    "font.size": 16,
    "figure.figsize": (8, 8),
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "axes.grid": True,
    "axes.grid.which": "both",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.3,
    "grid.color": "gray",
    "figure.subplot.left": 0.14,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

TWOPI = 2.0 * np.pi

# Units: mm
NPHIS = [15*2 // 2, 20*2 // 2, 58*2 // 2, 62*2 // 2,
         46*4 // 2, 54*4 // 2, 78*4 // 2, 82*4 // 2,
         48*2 // 2, 52*2 // 2, 80*2 // 2, 84*2 // 2,
         ]
INNER_RADII = [127.0, 167.0, 510.0, 550.0,
               819.0, 899.0, 1366.0, 1446.0,
               819.0, 899.0, 1366.0, 1446.0,
               ]
OUTER_RADII = [127.0 + 4.0, 167.0 + 4.0, 510.0 + 4.0, 550.0 + 4.0,
               819.0 + 12.0, 899.0 + 12.0, 1366.0 + 12.0, 1446.0 + 12.0,
               819.0 + 4.0, 899.0 + 4.0, 1366.0 + 4.0, 1446.0 + 4.0,
               ]
MODULE_WIDTHS = [30.1, 30.1, 30.1, 30.1,
                 30.1, 30.1, 30.1, 30.1,
                 60.2, 60.2, 60.2, 60.2,
                 ]
TEXTS = ["IT L0", "IT L2", "IT L4", "IT L6",
         "OT L0", "OT L2", "OT L4", "OT L6",
         "OT L0", "OT L2", "OT L4", "OT L6",
         ]

# OT 0
# NPHI = 46*4 // 2
# INNER_RADIUS = 819.0 # mm
# OUTER_RADIUS = 819.0 + 12.0 # mm

# OT 2
# NPHI = 54*4 // 2
# INNER_RADIUS = 899.0 # mm
# OUTER_RADIUS = 899.0 + 12.0 # mm

# OT 4
# NPHI = 78*4 // 2
# INNER_RADIUS = 1366.0 # mm
# OUTER_RADIUS = 1366.0 + 12.0 # mm

# OT 6
# NPHI = 82*4 // 2
# INNER_RADIUS = 1446.0 # mm
# OUTER_RADIUS = 1446.0 + 12.0 # mm

# MODULE_WIDTH = 30.1 # mm

PDF = "phi_modules.pdf"

def main():
    with PdfPages(PDF) as pdf:
        for (nphi, inner_radius, outer_radius, module_width) in zip(NPHIS, INNER_RADII, OUTER_RADII, MODULE_WIDTHS):
            df = make_modules(nphi, inner_radius, outer_radius, module_width)
            plot_modules(df, pdf, nphi, inner_radius, outer_radius, module_width, zoom=True)


    # dfs = [
    #     make_modules(nphi, inner_radius, outer_radius, module_width)
    #     for (nphi, inner_radius, outer_radius, module_width) in
    #     zip(NPHIS, INNER_RADII, OUTER_RADII, MODULE_WIDTHS)
    # ]
    # # df = make_modules(NPHI, INNER_RADIUS, OUTER_RADIUS, MODULE_WIDTH)
    # with PdfPages(PDF) as pdf:
    #     for df in dfs:
    #         plot_modules(df, PDF, nphi, inner_radius, outer_radius, module_width, zoom=True)


def make_modules(
        nphi: int,
        inner_radius: float,
        outer_radius: float,
        module_width: float,
    ) -> pd.DataFrame:

    dphi = TWOPI / nphi
    module_half_width = module_width / 2.0

    modules = []
    for i_mod in range(nphi):
        inner_phi = i_mod * dphi
        modules.append({
            "x0": inner_radius * np.cos(inner_phi) - module_half_width * np.sin(inner_phi),
            "y0": inner_radius * np.sin(inner_phi) + module_half_width * np.cos(inner_phi),
            "x1": inner_radius * np.cos(inner_phi) + module_half_width * np.sin(inner_phi),
            "y1": inner_radius * np.sin(inner_phi) - module_half_width * np.cos(inner_phi),
            "dphi": module_width / inner_radius, # small angle approximation: dl = r * dphi
        })

        outer_phi = inner_phi + (dphi / 2.0)
        modules.append({
            "x0": outer_radius * np.cos(outer_phi) - module_half_width * np.sin(outer_phi),
            "y0": outer_radius * np.sin(outer_phi) + module_half_width * np.cos(outer_phi),
            "x1": outer_radius * np.cos(outer_phi) + module_half_width * np.sin(outer_phi),
            "y1": outer_radius * np.sin(outer_phi) - module_half_width * np.cos(outer_phi),
            "dphi": module_width / outer_radius, # small angle approximation: dl = r * dphi
        })
    df = pd.DataFrame(modules)
    return df


# def calculate_coverage(NPHI, INNER_RADIUS, OUTER_RADIUS, MODULE_WIDTH) -> float:
#     # We're using the small angle approximation: dl = r * dphi
#     dphi_inner = MODULE_WIDTH / INNER_RADIUS * NPHI
#     dphi_outer = MODULE_WIDTH / OUTER_RADIUS * NPHI
#     coverage = (dphi_inner + dphi_outer) / TWOPI
#     return coverage


def plot(df: pd.DataFrame, pdfname: str):
    with PdfPages(pdfname) as pdf:
        plot_modules(df, pdf, zoom=False)
        plot_modules(df, pdf, zoom=True)


def plot_modules(
        df: pd.DataFrame,
        pdf: PdfPages,
        nphi: int,
        inner_radius: float,
        outer_radius: float,
        module_width: float,
        zoom: bool,
    ) -> None:
    # cov = calculate_coverage()
    cov = df["dphi"].sum() / TWOPI
    print(f"Coverage: {cov:.3f}x")

    # full view
    linewidth = 0.7 if not zoom else 5
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        ax.plot(
            [row["x0"], row["x1"]],
            [row["y0"], row["y1"]],
            linewidth=linewidth,
            color="dodgerblue",
        )
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(f"n(phi)={nphi}, coverage={cov:.3f} * " + r"$2\pi$")
    if zoom:
        dx = dy = module_width*3
        xlim = [inner_radius - dx, outer_radius + dx]
        ylim = [-dy, dy]
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    pdf.savefig()
    plt.close()

    # zoom
    # dx = dy = MODULE_WIDTH*3
    # xlim = [INNER_RADIUS - dx, INNER_RADIUS + dx]
    # ylim = [-dy, dy]
    # fig, ax = plt.subplots()
    # for _, row in df.iterrows():
    #     x0, x1, y0, y1 = row["x0"], row["x1"], row["y0"], row["y1"]
    #     if (
    #         (x0 < xlim[0] and x1 < xlim[0]) or
    #         (y0 < ylim[0] and y1 < ylim[0]) or
    #         (x0 > xlim[1] and x1 > xlim[1]) or
    #         (y0 > ylim[1] and y1 > ylim[1])
    #     ):
    #         continue
    #     ax.plot(
    #         [row["x0"], row["x1"]],
    #         [row["y0"], row["y1"]],
    #         linewidth=5,
    #         color="dodgerblue",
    #     )
    # ax.set_xlabel("x [mm]")
    # ax.set_ylabel("y [mm]")
    # ax.set_title(f"n(phi)={NPHI} gives coverage={cov:.3f}x")
    # ax.set_xlim(xlim)
    # ax.set_ylim(ylim)
    # pdf.savefig()
    # plt.close()


if __name__ == "__main__":
    main()
