import pyLCIO
import argparse
import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({'font.size': 16})

MCPARTICLE = "MCParticle"

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, required=True,
                        help="Path to the input slcio file")
    parser.add_argument("-o", type=str, default="mcparticles.pdf",
                        help="Path to the output pdf file")
    return parser.parse_args()


def main():

    ops = options()
    fnames = get_inputs(ops.i)
    if len(fnames) != 1:
        raise Exception("Please provide exactly one input file for plotting.")

    df = None
    for fname in fnames:
        df = get_mcparticles(fname)

    with PdfPages(ops.o) as pdf:
        plot_mcparticles(df, pdf)


def get_inputs(fpath: str) -> list[str]:
    inputs = []
    for fp in fpath.split(","):
        inputs.extend( glob.glob(fp) )
    if len(inputs) == 0:
        raise Exception(f"No input files found: {fpath}")
    return inputs


def get_mcparticles(fname: str):

    print(f"Reading {fname} ...")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)

    data = {
        "pdgid": [],
        "energy": [],
        "pt": [],
        "px": [],
        "py": [],
        "pz": []
    }

    for i_event, event in enumerate(reader):
        col = event.getCollection(MCPARTICLE)
        n_mc = col.getNumberOfElements()
        for i_part, part in enumerate(col):
            gen_status = part.getGeneratorStatus()
            is_sim = part.isCreatedInSimulation()
            pdgid, energy, mom = part.getPDG(), part.getEnergy(), part.getMomentum()
            px, py, pz = mom[0], mom[1], mom[2]
            pt = np.sqrt(px**2 + py**2)
            data["pdgid"].append(pdgid)
            data["energy"].append(energy)
            data["pt"].append(pt)
            data["px"].append(px)
            data["py"].append(py)
            data["pz"].append(pz)
    df = pd.DataFrame(data)
    return df

def plot_mcparticles(df: pd.DataFrame, pdf: PdfPages):
    print("Plotting MCParticles ...")

    for var in ["energy", "pt", "px", "py", "pz"]:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.hist(df[var], bins=np.linspace(-0.005, 0.005, 1000), histtype='stepfilled')
        ax.set_xlabel(var)
        ax.set_ylabel("Counts")
        ax.semilogy()
        ax.grid()
        ax.set_axisbelow(True)
        ax.tick_params(right=True, top=True, direction="in")
        fig.subplots_adjust(left=0.15, bottom=0.08, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()


if __name__ == "__main__":
    main()
