import argparse
from logging import root
import os
import pandas as pd
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

CEPH_XML = "/ceph/users/atuna/work/maia/k4geo/MuColl/MAIA/compact/MAIA_v0/InnerTrackerBarrelModuleDown.xml"
CEPH_PDF = "inner_tracker_barrel_material_stack.pdf"


def options():
    parser = argparse.ArgumentParser(description="Plot material stack from XML file")
    parser.add_argument("--xml", type=str, default=CEPH_XML, help="Path to the XML file containing material stack data")
    parser.add_argument("--pdf", type=str, default=CEPH_PDF, help="Path to the output PDF file for plots")
    return parser.parse_args()


def main():
    args = options()
    if not os.path.isfile(args.xml):
        raise FileNotFoundError(f"XML file not found: {args.xml}")

    # parse XML
    tree = ET.parse(args.xml)
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
    with PdfPages(args.pdf) as pdf:
        fig, ax = plt.subplots(figsize=(8, 8))
        bottom = 0
        for _, row in df.iterrows():
            thickness, material, info = row["thickness"], row["material"], row["info"]
            ax.bar("Module", thickness, bottom=bottom)
            text = f"{info} ({material})"
            ax.text(-0.39, bottom, text, ha="left", va="bottom", c="white", fontsize=text_scaling*thickness)
            bottom += thickness
        ax.set_ylabel("Thickness (mm)")
        ax.set_title("Inner Tracker Barrel Material Stack")
        ax.tick_params(bottom=False, right=True)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.05)
        pdf.savefig()
        plt.close()

if __name__ == "__main__":
    main()
