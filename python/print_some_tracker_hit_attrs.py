import argparse
import numpy as np
import pandas as pd

import pyLCIO

SIM_COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]

DIGI_COLLECTIONS = [
    "IBTrackerHits",
    "OBTrackerHits",
]

def main():
    ops = options()
    df = read_slcio(ops.i)
    print(df)
    print(df["hit_e"].describe())


def read_slcio(fname: str) -> pd.DataFrame:
    rows = []
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)
    for event in reader:
        print(f"Event number: {event.getEventNumber()}")
        for colname in SIM_COLLECTIONS + DIGI_COLLECTIONS:
            is_digi = colname in DIGI_COLLECTIONS
            if not colname in list(event.getCollectionNames()):
                print(f"Collection {colname} not found in event.")
                continue
            col = event.getCollection(colname)
            n_obj = len(col)
            print(f"Collection: {colname}, Number of elements: {n_obj}")
            for i_obj, obj in enumerate(col):
                if i_obj % 1e7 == 0:
                    print(f"{i_obj} / {n_obj}")
                rows.append({
                    "collection": colname,
                    "hit_x": obj.getPosition()[0],
                    "hit_y": obj.getPosition()[1],
                    "hit_z": obj.getPosition()[2],
                    "hit_e": obj.getEDep(),
                    "hit_t": obj.getTime(),
                    "hit_pathlength": obj.getPathLength() if hasattr(obj, 'getPathLength') else -1,
                    "hit_quality": np.int64(obj.getQuality()),
                    "hit_is_digi": is_digi,
                })

    return pd.DataFrame(rows)


def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, help="Input slcio file")
    return parser.parse_args()

if __name__ == "__main__":
    main()

