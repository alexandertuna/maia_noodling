import argparse
from logging import root
import os
import pandas as pd
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

import socket
hostname = socket.gethostname()
if "macbook" in hostname.lower():
    INNER_XML = "/Users/alexandertuna/Downloads/cms/muoncollider/k4geo/MuColl/MAIA/compact/MAIA_v0/InnerTrackerBarrelModuleDown.xml"
    OUTER_XML = "/Users/alexandertuna/Downloads/cms/muoncollider/k4geo/MuColl/MAIA/compact/MAIA_v0/OuterTrackerBarrelModuleDown.xml"
else:
    INNER_XML = "/ceph/users/atuna/work/maia/k4geo/MuColl/MAIA/compact/MAIA_v0/InnerTrackerBarrelModuleDown.xml"
    OUTER_XML = "/ceph/users/atuna/work/maia/k4geo/MuColl/MAIA/compact/MAIA_v0/OuterTrackerBarrelModuleDown.xml"
PDF = "tracker_barrel_material_stack.pdf"


def options():
    parser = argparse.ArgumentParser(description="Plot material stack from XML file")
    parser.add_argument("--inner_xml", type=str, default=INNER_XML, help="Path to the XML file containing inner tracker material stack data")
    parser.add_argument("--outer_xml", type=str, default=OUTER_XML, help="Path to the XML file containing outer tracker material stack data")
    parser.add_argument("--pdf", type=str, default=PDF, help="Path to the output PDF file for plots")
    return parser.parse_args()


def main():

    # check args
    args = options()
    xmls = [args.inner_xml, args.outer_xml]
    for xml in xmls:
        if not os.path.isfile(xml):
            raise FileNotFoundError(f"XML file not found: {xml}")

    # plot
    with PdfPages(args.pdf) as pdf:
        for xml in xmls:
            plot(xml, pdf)


def plot(xml, pdf):

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

if __name__ == "__main__":
    main()
