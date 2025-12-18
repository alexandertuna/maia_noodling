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

NPHI = 90
INNER_RADIUS = 800.0 # mm
OUTER_RADIUS = 804.0 # mm
MODULE_WIDTH = 30.1 # mm

PDF = "phi_modules.pdf"

def main():
    df = make_modules(NPHI, INNER_RADIUS, OUTER_RADIUS, MODULE_WIDTH)
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


def calculate_coverage() -> float:
    # We're using the small angle approximation: dl = r * dphi
    dphi_inner = MODULE_WIDTH / INNER_RADIUS * NPHI
    dphi_outer = MODULE_WIDTH / OUTER_RADIUS * NPHI
    coverage = (dphi_inner + dphi_outer) / TWOPI
    return coverage


def plot(df: pd.DataFrame, pdfname: str):
    with PdfPages(pdfname) as pdf:
        plot_modules(df, pdf)


def plot_modules(df: pd.DataFrame, pdf: PdfPages) -> None:
    cov = calculate_coverage()
    print(f"Coverage: {cov:.3f}x")

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
    ax.set_title(f"n(phi)={NPHI}, coverage={cov:.3f}x")
    pdf.savefig()
    plt.close()

    # zoom
    dx = dy = MODULE_WIDTH*3
    xlim = [INNER_RADIUS - dx, INNER_RADIUS + dx]
    ylim = [-dy, dy]
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        x0, x1, y0, y1 = row["x0"], row["x1"], row["y0"], row["y1"]
        if (
            (x0 < xlim[0] and x1 < xlim[0]) or
            (y0 < ylim[0] and y1 < ylim[0]) or
            (x0 > xlim[1] and x1 > xlim[1]) or
            (y0 > ylim[1] and y1 > ylim[1])
        ):
            continue
        ax.plot(
            [row["x0"], row["x1"]],
            [row["y0"], row["y1"]],
            linewidth=5,
            color="dodgerblue",
        )
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(f"n(phi)={NPHI} gives coverage={cov:.3f}x")
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    pdf.savefig()
    plt.close()


if __name__ == "__main__":
    main()
