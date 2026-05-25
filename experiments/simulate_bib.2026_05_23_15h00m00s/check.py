import pyLCIO
import numpy as np
import pandas as pd

FIVE_TESLA = [
    "neutrinoGun_digi_0_5T.slcio",
]

ZERO_TESLA = [
    "neutrinoGun_digi_0_0T.slcio",
]

SIM_COLS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
DIGI_COLS = [
    "IBTrackerHits",
    "OBTrackerHits",
]


def main():
    count_hits(FIVE_TESLA)
    count_hits(ZERO_TESLA)


def count_hits(fnames):
    n_sim = {col: 0 for col in SIM_COLS}
    n_digi = {col: 0 for col in DIGI_COLS}    
    for fname in fnames:
        print(f"Processing file {fname} ...")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(fname)
        for i_event, event in enumerate(reader):
            for col in SIM_COLS:
                n_sim[col] += len(event.getCollection(col))
            for col in DIGI_COLS:
                n_digi[col] += len(event.getCollection(col))

    for col in SIM_COLS:
        print(f"Total sim hits in {col}: {n_sim[col]}")
    for col in DIGI_COLS:
        print(f"Total digi hits in {col}: {n_digi[col]}")
    for (sim_col, digi_col) in zip(SIM_COLS, DIGI_COLS):
        ratio = n_digi[digi_col] / n_sim[sim_col]
        print(f"Ratio of {digi_col}/{sim_col}: {ratio:.4f}")
        

if __name__ == "__main__":
    main()

