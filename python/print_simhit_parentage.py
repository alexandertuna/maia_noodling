import pyLCIO

import argparse
import numpy as np
import logging
logger = logging.getLogger(__name__)

TRACKER = "OuterTrackerBarrelCollection"
MUON = 13
GEV_TO_KEV = 1e6
PDG_TO_NAME = {
    13: "muon",
    211: "pion",
    321: "kaon",
    2212: "proton",
    11: "electron",
    22: "photon",
}

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default="/ceph/users/atuna/work/maia/maia_noodling/samples/v01/muonGun_pT_0_10/muonGun_pT_0_10_sim_1.slcio",
                        help="Path to the input slcio file")
    parser.add_argument("-e", type=int, default=1, help="Number of events to process")
    parser.add_argument("--edep1kev", action="store_true", help="Filter for hits with energy deposition > 1 keV")
    parser.add_argument("--muons", action="store_true", help="Filter for muon hits only")
    parser.add_argument("--no-muons", action="store_true", help="Exclude muon hits")
    return parser.parse_args()


def main():

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ops = options()
    fname = ops.i
    n_events = ops.e
    only_muons = ops.muons
    exclude_muons = ops.no_muons
    edep1kev = ops.edep1kev

    logger.info(f"Reading {fname} ...")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)

    def log_parentage(mcp, level=0):
        if mcp is None:
            return
        indent = "  " * level
        pdg = abs(mcp.getPDG())
        name = PDG_TO_NAME[pdg]
        logger.info(f"{indent}PDG: {name}, N(parents): {len(mcp.getParents())}, E: {mcp.getEnergy():.3f} GeV")
        parents = mcp.getParents()
        if parents:
            log_parentage(parents[0], level + 1)

    for i_event, event in enumerate(reader):

        if i_event >= n_events:
            break
        logger.info(f"Event {i_event}")

        col = event.getCollection(TRACKER)

        for i_hit, hit in enumerate(col):

            if only_muons and np.abs(hit.getMCParticle().getPDG()) != MUON:
                continue
            if exclude_muons and np.abs(hit.getMCParticle().getPDG()) == MUON:
                continue
            if edep1kev and hit.getEDep() * GEV_TO_KEV < 1.0:
                continue

            logger.info(f"Event {i_event}, Sim hit {i_hit}:")
            log_parentage(hit.getMCParticle())




if __name__ == "__main__":
    main()
