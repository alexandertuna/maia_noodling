import pyLCIO

import os
import sys
import contextlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
plt.rcParams.update({"font.size": 16})

FILE_SIG = "/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_2p0_2p1/muonGun_pT_2p0_2p1_sim_100.slcio"
FILE_BKG = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_neutrinoGun.2026_01_21_13h10m00s/neutrinoGun_digi_n5p35_166.slcio"

COLL = "InnerTrackerBarrelCollection"
GEV_TO_KEV = 1e6
MM_TO_CM = 0.1
CM_TO_MM = 10.0

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"

import dd4hep, DDRec
dd4hep.setPrintLevel(dd4hep.PrintLevel.WARNING)

print(f"Opening {XML} geometry ... ")
@contextlib.contextmanager
def silence_c_stdout_stderr():
    # Flush Python buffers
    sys.stdout.flush()
    sys.stderr.flush()

    # Save original FDs
    old_stdout_fd = os.dup(1)
    old_stderr_fd = os.dup(2)

    # Redirect to /dev/null
    with open(os.devnull, "w") as devnull:
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            # Restore original FDs
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)
with silence_c_stdout_stderr():
    # Sorry for this context manager. dd4hep can be very noisy
    _detector = dd4hep.Detector.getInstance()
    _detector.fromCompact(XML)
    _surfman = DDRec.SurfaceManager(_detector)
    dets = {
        "InnerTrackerBarrelCollection": _detector.detector("InnerTrackerBarrel"),
        "OuterTrackerBarrelCollection": _detector.detector("OuterTrackerBarrel"),
    }
    _maps = {name: _surfman.map(det.name()) for name, det in dets.items()}



def main():
    df_sig = get_dataframe(FILE_SIG, COLL)
    df_bkg = get_dataframe(FILE_BKG, COLL)
    with PdfPages("energy_plots.pdf") as pdf:
        plot_energy(df_sig, df_bkg, f"sim hits ({COLL})", pdf)


def get_dataframe(fname: str, collection: str) -> pd.DataFrame:
    print(f"Reading file {fname}, collection {collection} ...")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    rows = []
    for event in reader:
        for hit in event.getCollection(collection):
            surf = _maps[collection].find(hit.getCellID0()).second
            pos = dd4hep.rec.Vector3D(hit.getPosition()[0] * MM_TO_CM,
                                      hit.getPosition()[1] * MM_TO_CM,
                                      hit.getPosition()[2] * MM_TO_CM)
            inside_bounds = surf.insideBounds(pos)
            row = {
                "hit_x": hit.getPosition()[0],
                "hit_y": hit.getPosition()[1],
                "hit_z": hit.getPosition()[2],
                "hit_e": hit.getEDep(),
                "hit_inside_bounds": inside_bounds,
            }
            rows.append(row)
    df = pd.DataFrame(rows)
    return df


def plot_energy(df_sig: pd.DataFrame, df_bkg: pd.DataFrame, label: str, pdf: PdfPages):
    color_sig = "dodgerblue"
    color_bkg = "orange"
    mask_sig = df_sig["hit_inside_bounds"]
    mask_bkg = df_bkg["hit_inside_bounds"]
    # bins = np.linspace(0, 1000, 1001)
    bins = np.logspace(np.log10(0.1), np.log10(1000), 100)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.hist(
        df_sig[mask_sig]["hit_e"] * GEV_TO_KEV,
        bins=bins,
        histtype="stepfilled",
        alpha=0.9,
        edgecolor="black",
        linewidth=1.0,
        color=color_sig,
        density=True,
        label="Muons",
    )
    ax.hist(
        df_bkg[mask_bkg]["hit_e"] * GEV_TO_KEV,
        bins=bins,
        histtype="stepfilled",
        alpha=0.5,
        edgecolor="black",
        linewidth=1.0,
        color=color_bkg,
        density=True,
        label="BIB",
    )
    ax.legend()
    ax.set_xlabel("Hit energy [keV]")
    ax.set_ylabel("Counts [normalized]")
    ax.semilogx()
    # ax.set_ylim(0.8, None)
    ax.set_title(f"Hit energy: {label}")
    ax.minorticks_on()
    ax.grid(which="both")
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
    ax.semilogy()
    pdf.savefig()
    plt.close()




if __name__ == "__main__":
    main()
