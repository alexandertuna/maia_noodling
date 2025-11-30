import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

import pyLCIO

BFIELD = 5.0  # Tesla
NEV = 2
PDF = "tracks_and_clusters.pdf"
TRACKS = "SiTracks_Refitted"
CLUSTERS = "PandoraClusters"
MCPARTICLES = "MCParticle"

def main():
    ops = options()
    if not ops.i:
        raise ValueError("Input LCIO file is required. Use -i to specify the file path")

    tracks, clusters, mcparticles = get_dataframes(ops.i, NEV)

    with PdfPages(PDF) as pdf:
        plot(tracks, clusters, mcparticles, pdf)


def track_to_pt_eta_phi(track):
    omega, tan_lambda, phi = track.getOmega(), track.getTanLambda(), track.getPhi()
    pt = 0.3 * BFIELD / abs(omega)
    eta = np.arcsinh(1.0 / tan_lambda)
    return pt, eta, phi


def cluster_to_energy_eta_phi(cluster):
    energy = cluster.getEnergy()
    position = cluster.getPositionVec()
    x, y, z = position.X(), position.Y(), position.Z()
    rt = np.sqrt(x**2 + y**2)
    theta = np.arctan2(rt, z)
    eta = -np.log(np.tan(theta / 2))
    phi = np.arctan2(y, x)
    return energy, eta, phi

def mcparticle_to_pt_eta_phi_pdg(mcparticle):
    momentum = mcparticle.getMomentum()
    px, py, pz = momentum[0], momentum[1], momentum[2]
    pt = np.sqrt(px**2 + py**2)
    theta = np.arctan2(pt, pz)
    eta = -np.log(np.tan(theta / 2)) if theta != 0 else 0.0
    phi = np.arctan2(py, px)
    pdg = mcparticle.getPDG()
    return pt, eta, phi, pdg

# def track_params_to_pt_eta_phi(omega, tan_lambda, phi, B=5.0):
#     pt = 0.3 * B / abs(omega)
#     eta = np.arcsinh(1.0 / tan_lambda)
#     return pt, eta, phi

def get_dataframes(fname: str, nev: int):
    tracks_data = []
    clusters_data = []
    mcparticles_data = []
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    for i_event, event in enumerate(reader):
        if i_event >= nev:
            break
        print(f"Processing event {i_event}")
        tracks = event.getCollection(TRACKS)
        clusters = event.getCollection(CLUSTERS)
        mcparticles = event.getCollection(MCPARTICLES)
        for track in tracks:
            pt, eta, phi = track_to_pt_eta_phi(track)
            tracks_data.append({"i_event": i_event,
                                "pt": pt,
                                "eta": eta,
                                "phi": phi,
                                })
        for cluster in clusters:
            energy, eta, phi = cluster_to_energy_eta_phi(cluster)
            clusters_data.append({"i_event": i_event,
                                  "energy": energy,
                                  "eta": eta,
                                  "phi": phi,
                                  })
        for mcparticle in mcparticles:
            pt, eta, phi, pdg = mcparticle_to_pt_eta_phi_pdg(mcparticle)
            mcparticles_data.append({"i_event": i_event,
                                     "pt": pt,
                                     "eta": eta,
                                     "phi": phi,
                                     "pdg": pdg,
                                     })
            
    return [
        pd.DataFrame(tracks_data),
        pd.DataFrame(clusters_data),
        pd.DataFrame(mcparticles_data),
    ]


def plot(tracks: pd.DataFrame,
         clusters: pd.DataFrame,
         mcparticles: pd.DataFrame,
         pdf: PdfPages,
         ):
    print("Events: ", tracks["i_event"].unique())
    print("Events: ", clusters["i_event"].unique())
    print("Events: ", mcparticles["i_event"].unique())
    for i_event in mcparticles["i_event"].unique():
        print(f"Plotting event {i_event}")
        trk = tracks[tracks["i_event"] == i_event]
        clu = clusters[clusters["i_event"] == i_event]
        mcp = mcparticles[mcparticles["i_event"] == i_event]
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.scatter(clu["eta"], clu["phi"], label="Clusters", color="red", alpha=0.5)
        ax.scatter(trk["eta"], trk["phi"], label="Tracks", color="blue", alpha=0.5)
        ax.scatter(mcp["eta"], mcp["phi"], label="MC Particles", color="green", alpha=0.5)
        ax.set_xlim(-7, 7)
        ax.set_ylim(-4, 4)
        ax.set_xlabel("Eta")
        ax.set_ylabel("Phi")
        ax.set_title(f"Event {i_event}")
        ax.grid(True)
        ax.legend()
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
