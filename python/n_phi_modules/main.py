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
    "figure.subplot.left": 0.15,
    "figure.subplot.bottom": 0.12,
    "figure.subplot.right": 0.95,
    "figure.subplot.top": 0.95,
})

TWOPI = 2.0 * np.pi

NPHI = 100
INNER_RADIUS = 800.0 # mm
OUTER_RADIUS = 804.0 # mm
MODULE_WIDTH = 30.1 # mm

PDF = "phi_modules.pdf"

def main():
    df = make_modules(NPHI, INNER_RADIUS, OUTER_RADIUS, MODULE_WIDTH)
    print(df)
    plot(df, PDF)


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
        })

        outer_phi = inner_phi + (dphi / 2.0)
        modules.append({
            "x0": outer_radius * np.cos(outer_phi) - module_half_width * np.sin(outer_phi),
            "y0": outer_radius * np.sin(outer_phi) + module_half_width * np.cos(outer_phi),
            "x1": outer_radius * np.cos(outer_phi) + module_half_width * np.sin(outer_phi),
            "y1": outer_radius * np.sin(outer_phi) - module_half_width * np.cos(outer_phi),
        })
    df = pd.DataFrame(modules)
    return df


def plot(df: pd.DataFrame, pdfname: str):
    with PdfPages(pdfname) as pdf:
        plot_modules(df, pdf)


def plot_modules(df: pd.DataFrame, pdf: PdfPages) -> None:
    # full view
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        ax.plot(
            [row["x0"], row["x1"]],
            [row["y0"], row["y1"]],
            linewidth=0.7,
            color="dodgerblue",
        )
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    pdf.savefig()
    plt.close()

    # zoom
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        ax.plot(
            [row["x0"], row["x1"]],
            [row["y0"], row["y1"]],
            linewidth=3,
            color="dodgerblue",
        )
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_xlim([INNER_RADIUS*0.95, OUTER_RADIUS*1.05])
    ax.set_ylim([-MODULE_WIDTH*3, MODULE_WIDTH*3])
    pdf.savefig()
    plt.close()


if __name__ == "__main__":
    main()
