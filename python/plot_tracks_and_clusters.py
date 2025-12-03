import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

import pyLCIO

BFIELD = 5.0  # Tesla
MIN_PT = 1.0 # GeV
NEV = 10
PDF = "tracks_and_clusters.pdf"
TRACKERS = [
    "VBTrackerHits",
    "VETrackerHits",
    "IBTrackerHits",
    "IETrackerHits",
    "OBTrackerHits",
    "OETrackerHits",
]
CALORIMETERS = [
    "EcalBarrelCollectionSel",
    "EcalEndcapCollectionSel",
    "HcalBarrelCollectionSel",
    "HcalEndcapCollectionSel",
]
TRACKS = "SiTracks_Refitted"
CLUSTERS = "PandoraClusters"
MCPARTICLES = "MCParticle"

def main():
    ops = options()
    if not ops.i:
        raise ValueError("Input LCIO file is required. Use -i to specify the file path")

    tracks, clusters, mcparticles, tracker_hits, calo_hits = get_dataframes(ops.i, NEV)

    with PdfPages(PDF) as pdf:
        plot(tracks, clusters, mcparticles, tracker_hits, calo_hits, pdf)


def hit_attrs(hit):
    position = hit.getPosition()
    x, y, z = position[0], position[1], position[2]
    rt = np.sqrt(x**2 + y**2)
    theta = np.arctan2(rt, z)
    eta = -np.log(np.tan(theta / 2))
    phi = np.arctan2(y, x)
    return {
        "eta": eta,
        "phi": phi,
    }


def track_attrs(track):
    omega, tan_lambda, phi = track.getOmega(), track.getTanLambda(), track.getPhi()
    pt = 0.3 * BFIELD / abs(omega)
    theta = np.arcsinh(1.0 / tan_lambda)
    eta = -np.log(np.tan(theta / 2))
    return {
        "pt": pt,
        "eta": eta,
        "phi": phi,
    }


def cluster_attrs(cluster):
    energy = cluster.getEnergy()
    position = cluster.getPositionVec()
    x, y, z = position.X(), position.Y(), position.Z()
    rt = np.sqrt(x**2 + y**2)
    theta = np.arctan2(rt, z)
    eta = -np.log(np.tan(theta / 2))
    phi = np.arctan2(y, x)
    et = energy * np.sin(theta)
    return {
        "energy": energy,
        "eta": eta,
        "phi": phi,
        "et": et,
    }

def is_high_energy(mcparticle) -> bool:
    return np.sqrt(mcparticle.getMomentum()[0]**2 + \
                   mcparticle.getMomentum()[1]**2) > MIN_PT

def is_visible_final_state(mcparticle) -> bool:
    """
    mc->getGeneratorStatus() == 1
    !mc->isCreatedInSimulation()
    int pdg = mc->getPDG();
    if (abs(pdg) == 12 || abs(pdg) == 14 || abs(pdg) == 16) continue;   // ν
    bool isChargedHadron =
        abs(pdg) == 211  ||  // π±
        abs(pdg) == 321  ||  // K±
        abs(pdg) == 2212;    // p, p̄

    bool isLepton =
        abs(pdg) == 11 || abs(pdg) == 13;   // e, μ

    bool isPhoton = (pdg == 22);

    if (!(isChargedHadron || isLepton || isPhoton)) continue;
    """
    if mcparticle.getGeneratorStatus() != 1:
        return False
    if mcparticle.isCreatedInSimulation():
        return False
    pdg = abs(mcparticle.getPDG())
    if pdg in (12, 14, 16):
        return False
    if pdg in (211, 321, 2212, 11, 13, 22):
        return True
    return False


def mcparticle_attrs(mcparticle):
    momentum = mcparticle.getMomentum()
    px, py, pz = momentum[0], momentum[1], momentum[2]
    pt = np.sqrt(px**2 + py**2)
    theta = np.arctan2(pt, pz)
    eta = -np.log(np.tan(theta / 2)) if theta != 0 else 0.0
    phi = np.arctan2(py, px)
    pdg = mcparticle.getPDG()
    charge = mcparticle.getCharge()
    return {
        "pt": pt,
        "eta": eta,
        "phi": phi,
        "pdg": pdg,
        "charge": charge,
    }


def get_dataframes(fname: str, nev: int):
    tracks_data = []
    clusters_data = []
    mcparticles_data = []
    tracker_hits_data = []
    calo_hits_data = []
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    for i_event, event in enumerate(reader):
        if i_event == 0:
            names_per_row = 4
            for i_name, name in enumerate(event.getCollectionNames()):
                print(name)
        if i_event >= nev:
            break
        print(f"Processing event {i_event}")
        tracks = event.getCollection(TRACKS)
        clusters = event.getCollection(CLUSTERS)
        mcparticles = event.getCollection(MCPARTICLES)
        trackers = [event.getCollection(tracker) for tracker in TRACKERS]
        calos = [event.getCollection(calo) for calo in CALORIMETERS]
        for track in tracks:
            tracks_data.append({"i_event": i_event, **track_attrs(track)})
        for cluster in clusters:
            if cluster.getEnergy() < MIN_PT:
                continue
            clusters_data.append({"i_event": i_event, **cluster_attrs(cluster)})
        for mcparticle in mcparticles:
            if not is_visible_final_state(mcparticle):
                continue
            if not is_high_energy(mcparticle):
                continue
            mcparticles_data.append({"i_event": i_event, **mcparticle_attrs(mcparticle)})
        for tracker in trackers:
            for hit in tracker:
                tracker_hits_data.append({"i_event": i_event, **hit_attrs(hit)})
        for calo in calos:
            for hit in calo:
                calo_hits_data.append({"i_event": i_event, **hit_attrs(hit)})

    return [
        pd.DataFrame(tracks_data),
        pd.DataFrame(clusters_data),
        pd.DataFrame(mcparticles_data),
        pd.DataFrame(tracker_hits_data),
        pd.DataFrame(calo_hits_data),
    ]


def plot(tracks: pd.DataFrame,
         clusters: pd.DataFrame,
         mcparticles: pd.DataFrame,
         tracker_hits: pd.DataFrame,
         calo_hits: pd.DataFrame,
         pdf: PdfPages,
         ):
    print("Events: ", mcparticles["i_event"].unique())
    for i_event in mcparticles["i_event"].unique():
        print(f"Plotting event {i_event}")

        tracker = tracker_hits[tracker_hits["i_event"] == i_event]
        bins = [np.linspace(-5, 5, 101),
                np.linspace(-4, 4, 101)]
        fig, ax = plt.subplots(figsize=(8, 8))
        _, _, _, im = ax.hist2d(tracker["eta"], tracker["phi"], bins=bins, cmap="hot", cmin=0.5)
        fig.colorbar(im, ax=ax, label="Tracker hits")
        ax.set_xlabel("Eta")
        ax.set_ylabel("Phi")
        ax.set_title(f"Event {i_event}, tracker hits")
        ax.grid(True)
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


        calo = calo_hits[calo_hits["i_event"] == i_event]
        bins = [np.linspace(-5, 5, 101),
                np.linspace(-4, 4, 101)]
        fig, ax = plt.subplots(figsize=(8, 8))
        _, _, _, im = ax.hist2d(calo["eta"], calo["phi"], bins=bins, cmap="hot", cmin=0.5)
        fig.colorbar(im, ax=ax, label="Calo hits")
        ax.set_xlabel("Eta")
        ax.set_ylabel("Phi")
        ax.set_title(f"Event {i_event}, calo hits")
        ax.grid(True)
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


        trk = tracks[tracks["i_event"] == i_event]
        clu = clusters[clusters["i_event"] == i_event]
        mcp = mcparticles[mcparticles["i_event"] == i_event]
        fig, ax = plt.subplots(figsize=(8, 8))
        charged = mcp[mcp["charge"] != 0]
        neutral = mcp[mcp["charge"] == 0]
        ax.scatter(charged["eta"], charged["phi"], label="MC Charged", color="black", alpha=0.8)
        ax.scatter(neutral["eta"], neutral["phi"], label="MC Neutral", color="gray", alpha=0.8)
        ax.scatter(clu["eta"], clu["phi"], label="Clusters", color="red", alpha=0.5)
        ax.scatter(trk["eta"], trk["phi"], label="Tracks", color="blue", alpha=0.5)
        ax.set_xlim(-5, 5)
        ax.set_ylim(-4, 4)
        ax.set_xlabel("Eta")
        ax.set_ylabel("Phi")
        ax.set_title(f"Event {i_event}")
        ax.grid(True)
        ax.set_axisbelow(True)
        ax.legend()
        fig.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()


def plot_old(fname: str, nev: int, pdf: PdfPages):
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    for i_event, event in enumerate(reader):
        if i_event >= nev:
            break
        print(f"Processing event {i_event}")
        # print(event.getCollectionNames())
        tracks = event.getCollection(TRACKS)
        clusters = event.getCollection(CLUSTERS)
        mcparticles = event.getCollection(MCPARTICLES)
        print(f"Number of tracks: {len(tracks)}")
        print(f"Number of clusters: {len(clusters)}")
        print(f"Number of MC particles: {len(mcparticles)}")
        # for track in tracks:
        #     pt, eta, phi = track_to_pt_eta_phi(track)
        #     print(f"Track parameters: pt = {pt:.3f}, eta = {eta:.3f}, phi = {phi:.3f}")
        track_etas = [eta for _, eta, _ in (track_to_pt_eta_phi(track) for track in tracks)]
        track_phis = [phi for _, _, phi in (track_to_pt_eta_phi(track) for track in tracks)]
        cluster_etas = [eta for _, eta, _ in (cluster_to_energy_eta_phi(cluster) for cluster in clusters)]
        cluster_phis = [phi for _, _, phi in (cluster_to_energy_eta_phi(cluster) for cluster in clusters)]
        mcparticle_etas = [eta for pt, eta, _, _ in (mcparticle_to_pt_eta_phi_pdg(mcparticle) for mcparticle in mcparticles) if pt > 100]
        mcparticle_phis = [phi for pt, _, phi, _ in (mcparticle_to_pt_eta_phi_pdg(mcparticle) for mcparticle in mcparticles) if pt > 100]
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.scatter(cluster_etas, cluster_phis, label="Clusters", color="red", alpha=0.5)
        ax.scatter(track_etas, track_phis, label="Tracks", color="blue", alpha=0.5)
        ax.scatter(mcparticle_etas, mcparticle_phis, label="MC Particles", color="green", alpha=0.5)
        ax.set_xlim(-5, 5)
        ax.set_ylim(-np.pi, np.pi)
        ax.set_xlabel("Eta")
        ax.set_ylabel("Phi")
        ax.set_title(f"Event {i_event}")
        ax.grid(True)
        ax.legend()
        pdf.savefig()
        plt.close()


def options():
    parser = argparse.ArgumentParser(description="Plot tracks and clusters from a LCIO file")
    parser.add_argument("-i", type=str, help="Path to the input LCIO file")
    return parser.parse_args()

if __name__ == "__main__":
    main()
