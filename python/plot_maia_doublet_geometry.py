import pyLCIO
import argparse
import os
import glob
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
import xml.etree.ElementTree as ET
rcParams.update({'font.size': 16})

FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_digi_10*.slcio"

INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5

InnerTracker_Barrel_DoubleLayer_Gap = 2.0 # mm
OuterTracker_Barrel_DoubleLayer_Gap = 6.0 # mm

TRACKERS = [
    # "VertexBarrelCollection",
    # "VertexEndcapCollection",
    "InnerTrackerBarrelCollection",
    # "InnerTrackerEndcapCollection",
    "OuterTrackerBarrelCollection",
    # "OuterTrackerEndcapCollection",
]

INNER_XML = "/ceph/users/atuna/work/maia/k4geo/MuColl/MAIA/compact/MAIA_v0/InnerTrackerBarrelModuleDown.xml"
OUTER_XML = "/ceph/users/atuna/work/maia/k4geo/MuColl/MAIA/compact/MAIA_v0/OuterTrackerBarrelModuleDown.xml"

NSENSORS = {
    INNER_TRACKER_BARREL: [32, 32, 32, 32, 46, 46, 46, 46],
    OUTER_TRACKER_BARREL: [84, 84, 84, 84, 84, 84, 84, 84],
}


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default=FNAME,
                        help="Path to input slcio file")
    parser.add_argument("--inner_xml", type=str, default=INNER_XML,
                        help="Path to XML file with inner tracker material stack data")
    parser.add_argument("--outer_xml", type=str, default=OUTER_XML,
                        help="Path to XML file with outer tracker material stack data")
    parser.add_argument("--pdf", type=str, default="maia_doublet_v0.pdf",
                        help="Path to output PDF file")
    parser.add_argument("--plot_xy", action="store_true",
                        help="Enable plotting of XY geometry")
    parser.add_argument("--plot_rz", action="store_true",
                        help="Enable plotting of RZ geometry")
    parser.add_argument("--plot_xml", action="store_true",
                        help="Enable plotting of XML material stacks")
    return parser.parse_args()


def main():

    ops = options()
    if not (ops.plot_xy or ops.plot_rz or ops.plot_xml):
        raise Exception("No plotting options selected! Use --plot_xy, --plot_rz, or --plot_xml.")

    # parse slcio files
    if ops.plot_xy or ops.plot_rz:
        fnames = get_inputs(ops.i)
        hits = get_hits(fnames)
        hits = post_process(hits)
        print(hits)

    # parse xmls?
    if ops.plot_xml:
        xmls = [ops.inner_xml, ops.outer_xml]
        for xml in xmls:
            if not os.path.isfile(xml):
                raise FileNotFoundError(f"XML file not found: {xml}")
    else:
        xmls = []

    # make plots and save to pdf
    with PdfPages(ops.pdf) as pdf:
        if ops.plot_xy:
            plot_barrel_xy(hits, pdf)
        if ops.plot_rz:
            plot_barrel_rz(hits, pdf)
        for xml in xmls:
            plot_material_xml(xml, pdf)


def get_inputs(fpath: str) -> list[str]:
    inputs = []
    for fp in fpath.split(","):
        inputs.extend( glob.glob(fp) )
    if len(inputs) == 0:
        raise Exception(f"No input files found: {fpath}")
    return inputs


def get_hits(fnames: list[str]) -> pd.DataFrame:

    hits = []
    for fname in fnames:
        print(f"Reading {fname} ...")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(fname)
        for event in reader:
            for colname in TRACKERS:
                for hit in event.getCollection(colname):
                    hits.append( [
                        hit.getPositionVec().X(),
                        hit.getPositionVec().Y(),
                        hit.getPositionVec().Z(),
                        hit.getEDep(),
                        hit.getPathLength(),
                        hit.getCellID0(),
                    ] )

    return pd.DataFrame(np.array(hits), columns=["x", "y", "z", "e", "dx", "cellid0"])


def post_process(df: pd.DataFrame) -> pd.DataFrame:
    print("Post-processing hits ...")
    df["cellid0"] = df["cellid0"].astype(np.int64)
    df["r"] = np.sqrt(df["x"]**2 + df["y"]**2)
    df["system"] = np.right_shift(df["cellid0"], 0) & 0b1_1111
    df["side"] = np.right_shift(df["cellid0"], 5) & 0b11
    df["layer"] = np.right_shift(df["cellid0"], 7) & 0b11_1111
    df["module"] = np.right_shift(df["cellid0"], 13) & 0b111_1111_1111
    df["sensor"] = np.right_shift(df["cellid0"], 24) & 0b1111_1111
    df["module_mod_2"] = df["module"] % 2
    return df


def plot_material_xml(xml, pdf):

    is_inner = "inner" in xml.lower()

    # parse XML
    tree = ET.parse(xml)
    root = tree.getroot()

    # make dataframe of materials
    df = pd.DataFrame([
        comp.attrib for comp in root.findall("module_component")
    ])
    df["thickness"] = df["thickness"].str.replace("*mm", "").astype(float)
    df["sensitive"] = df["sensitive"].str.lower().eq("true")
    print(df)

    # stacked bar chart
    text_scaling = 100
    fig, ax = plt.subplots(figsize=(8, 8))
    bottom = 0
    for _, row in df.iterrows():
        thickness, material, info = row["thickness"], row["material"], row["info"]
        ax.bar("Module", thickness, bottom=bottom)
        text = f"{info} ({material})"
        text = text.replace("Structure and cooling: ", "")
        fontsize = min(text_scaling*thickness, 30)
        ax.text(-0.39, bottom, text, ha="left", va="bottom", c="white", fontsize=fontsize)
        bottom += thickness
    ax.set_ylabel("Thickness (mm)")
    ax.set_title(f"{'Inner' if is_inner else 'Outer'} Tracker Barrel Material Stack")
    ax.tick_params(bottom=False, right=True)
    fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.05)
    pdf.savefig()
    plt.close()


def plot_barrel_rz(df: pd.DataFrame, pdf: PdfPages) -> None:

    colors = {
        INNER_TRACKER_BARREL: [
            "green",
            "purple",
            "green",
            "purple",
            "green",
            "purple",
            "green",
            "purple",
        ],
        OUTER_TRACKER_BARREL: [
            "blue",
            "red",
            "blue",
            "red",
            "blue",
            "red",
            "blue",
            "red",
        ],
    }

    columns = [
        "system",
        "layer",
        "module_mod_2",
        "sensor",
    ]
    ha, va = "left", "bottom"

    for it, [zmin, zmax, rmin, rmax] in enumerate([
        [-1550, 1550, 0, 1550],
    ]):

        print(f"Plotting barrel rz section {it} ...")
        fig, ax = plt.subplots(figsize=(8, 8))
        grouped = df.groupby(columns)
        for (system, layer, module_mod_2, sensor), group in grouped:

            # get rough boundaries of sensor
            outlier = np.abs(group["r"] - group["r"].median()) > 5 # mm
            z_min = group["z"][~outlier].min()
            z_max = group["z"][~outlier].max()
            r_avg = group["r"][~outlier].median()

            # plot
            lw = get_line_width(system, zoom=False)
            col = colors[system][layer]
            ax.plot([z_min, z_max],
                    [r_avg, r_avg],
                    c=col,
                    lw=lw,
                    alpha = 1.0 if sensor % 2 == 0 else 0.7,
                    )

            # text annotations
            if layer % 2 == 1 and module_mod_2 == 1 and sensor % 2 == 0:
                ax.text(z_min, r_avg, f"{int(sensor):02}", ha=ha, va=va, fontsize=3.5)
            if layer % 2 == 0 and sensor == 0 and module_mod_2 == 0:
                if system == INNER_TRACKER_BARREL:
                    dr, dz = -5, -260
                    acronym = "IT"
                elif system == OUTER_TRACKER_BARREL:
                    dr, dz = 0, -280
                    acronym = "OT"
                else:
                    raise Exception("What?")
                ax.text(z_min + dz, r_avg + dr, f"{acronym}, L{layer}-L{layer+1}", ha=ha, va=va, fontsize=8)
            if sensor == NSENSORS[system][layer] - 1 and layer % 2 == 0: # and module_mod_2 == 0:
                dz, dr = 10, 0
                if system == INNER_TRACKER_BARREL:
                    dr = -7 if module_mod_2 == 0 else -2
                ax.text(z_max + dz, r_avg + dr, f"Module % 2 = {module_mod_2}", ha=ha, va=va, fontsize=3)

        ax.text(0.02, 1.01, '"Sensor" (z-coordinate)', transform=ax.transAxes)
        ax.grid(which="both", linestyle="-", alpha=0.2, c="black", lw=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(top=True, right=True, direction="in")
        ax.set_xlabel("Sim. hit z [mm]")
        ax.set_ylabel("Sim. hit r [mm]")
        ax.set_xlim(zmin, zmax)
        ax.set_ylim(rmin, rmax)
        fig.subplots_adjust(right=0.97, left=0.16, bottom=0.09, top=0.95)
        pdf.savefig()
        plt.close()



def plot_barrel_xy(df: pd.DataFrame, pdf: PdfPages) -> None:

    colors = {
        INNER_TRACKER_BARREL: [
            "green",
            "purple",
            "green",
            "purple",
            "green",
            "purple",
            "green",
            "purple",
        ],
        OUTER_TRACKER_BARREL: [
            "blue",
            "red",
            "blue",
            "red",
            "blue",
            "red",
            "blue",
            "red",
        ],
    }

    columns = [
        "system",
        "layer",
        "module",
    ]

    for it, [xmin, xmax, ymin, ymax] in enumerate([
        [-1550, 1550, -1550, 1550],
        [-1550, 1550, -1550, 1550],
        [100, 195, -50, 50],
        [480, 580, -50, 50],
        [765, 955, -50, 50],
        [1315, 1505, -50, 50],
    ]):
        print(f"Plotting barrel XY section {it} ...")
        fig, ax = plt.subplots(figsize=(8, 8))
        grouped = df.groupby(columns)
        for (system, layer, module), group in grouped:
            x_corners, y_corners = get_points_for_line(group)
            lw = get_line_width(system, zoom=(it > 1))
            ax.plot(x_corners,
                    y_corners,
                    c=colors[system][layer],
                    lw=lw,
                    )

        if it == 0:
            # draw entire xy with layer annotations
            ha = "center"
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            ax.text(0, 200, "IT, L0-L3", ha=ha)
            ax.text(0, 580, "IT, L4-L7", ha=ha)
            ax.text(0, 940, "OT, L0-L3", ha=ha)
            ax.text(0, 1230, "OT, L4-L7", ha=ha)
            ax.text(0.02, 1.01, '"Layer" (r-coordinate)', transform=ax.transAxes, fontsize=16)
            ax.text(0.74, 1.01, now, transform=ax.transAxes, fontsize=10)
        elif it == 1:
            # draw entire xy with layer and module annotations
            ha = "center"
            for (system, layer, module), group in grouped:
                if layer not in [0, 3, 4, 7]:
                    continue
                x_corners, y_corners = get_points_for_line(group)
                x_avg, y_avg = np.mean(x_corners), np.mean(y_corners)
                r_avg, phi = np.sqrt(x_avg**2 + y_avg**2), np.arctan2(y_avg, x_avg)
                if system == INNER_TRACKER_BARREL:
                    dr = 30 if layer in [3, 7] else -30
                elif system == OUTER_TRACKER_BARREL:
                    dr = 40 if layer in [3, 7] else -40
                else:
                    raise Exception("What?")
                x_new, y_new = (r_avg + dr) * np.cos(phi), (r_avg + dr) * np.sin(phi)
                ax.text(x_new, y_new, f"{module:03}", ha="center", va="center", fontsize=3, rotation=np.degrees(phi))
            ax.text(0.02, 1.01, '"Module" (phi-coordinate)', transform=ax.transAxes, fontsize=16)
        elif it == 2:
            va = "center"
            gap = InnerTracker_Barrel_DoubleLayer_Gap
            gap = f"Doublet gap: {int(gap)}mm"
            ax.text(115, 0, "IT, L0", va=va)
            ax.text(131, 0, "IT, L1", va=va)
            ax.text(155, 0, "IT, L2", va=va)
            ax.text(172, 0, "IT, L3", va=va)
            ax.text(0.02, 1.01, gap, transform=ax.transAxes)
        elif it == 3:
            va = "center"
            gap = InnerTracker_Barrel_DoubleLayer_Gap
            gap = f"Doublet gap: {int(gap)}mm"
            ax.text(498, 0, "IT, L4", va=va)
            ax.text(515, 0, "IT, L5", va=va)
            ax.text(538, 0, "IT, L6", va=va)
            ax.text(555, 0, "IT, L7", va=va)
            ax.text(0.02, 1.01, gap, transform=ax.transAxes)
        elif it == 4:
            va = "center"
            gap = OuterTracker_Barrel_DoubleLayer_Gap
            gap = f"Doublet gap: {int(gap)}mm"
            ax.text(790, 0, "OT, L0", va=va)
            ax.text(833, 0, "OT, L1", va=va)
            ax.text(870, 0, "OT, L2", va=va)
            ax.text(915, 0, "OT, L3", va=va)
            ax.text(0.02, 1.01, gap, transform=ax.transAxes)
        elif it == 5:
            va = "center"
            gap = OuterTracker_Barrel_DoubleLayer_Gap
            gap = f"Doublet gap: {int(gap)}mm"
            ax.text(1335, 0, "OT, L4", va=va)
            ax.text(1380, 0, "OT, L5", va=va)
            ax.text(1415, 0, "OT, L6", va=va)
            ax.text(1460, 0, "OT, L7", va=va)
            ax.text(0.02, 1.01, gap, transform=ax.transAxes)
        else:
            raise Exception("What?")

        ax.grid(which="both", linestyle="-", alpha=0.2, c="black", lw=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(top=True, right=True, direction="in")
        ax.set_xlabel("Sim. hit x [mm]")
        ax.set_ylabel("Sim. hit y [mm]")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        fig.subplots_adjust(right=0.97, left=0.16, bottom=0.09, top=0.95)
        pdf.savefig()
        plt.close()


def get_line_width(system: int, zoom: bool) -> float:
    multiplier = 10.0 if zoom else 1.0
    if system == INNER_TRACKER_BARREL:
        return 0.3 * multiplier
    elif system == OUTER_TRACKER_BARREL:
        return 0.7 * multiplier
    else:
        raise Exception(f"Unknown system: {system}")


def get_points_for_line(df: pd.DataFrame) -> tuple[list[float], list[float]]:
    # Assume the points form a rectangle with an angle
    # Find the center of the rectangle (median x and y)
    # Rotate relative to the origin (0, 0) to align with axes
    # Find the min and max x and y in the rotated frame
    # Rotate back to original frame
    x_center = df["x"].median()
    y_center = df["y"].median()
    angle = np.arctan2(y_center, x_center)
    cos_angle = np.cos(-angle)
    sin_angle = np.sin(-angle)
    xp = cos_angle * df["x"] - sin_angle * df["y"]
    yp = sin_angle * df["x"] + cos_angle * df["y"]
    outlier = np.abs(xp - xp.median()) > 5 # mm
    xp_avg = xp[~outlier].median()
    yp_min = yp[~outlier].min()
    yp_max = yp[~outlier].max()
    x_corners = []
    y_corners = []
    for xp_c, yp_c in [(xp_avg, yp_min),
                       (xp_avg, yp_max),
                       ]:
        x_orig = cos_angle * xp_c + sin_angle * yp_c
        y_orig = -sin_angle * xp_c + cos_angle * yp_c
        x_corners.append(x_orig)
        y_corners.append(y_orig)
    return x_corners, y_corners


def get_color() -> str:
    if len(TRACKERS) == 1:
        tr = TRACKERS[0]
        if "Vertex" in tr:
            return "blue"
        elif "Inner" in tr:
            return "red"
        elif "Outer" in tr:
            return "green"
        raise Exception(f"What? {tr}")
    return "black"


if __name__ == "__main__":
    main()
