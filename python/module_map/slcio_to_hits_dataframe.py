"""
CellID encoding for IBTrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
CellID encoding for IETrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
CellID encoding for OBTrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
CellID encoding for OETrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
"""

import pyLCIO
import numpy as np
import pandas as pd
from tqdm import tqdm
import os
import multiprocessing as mp

from constants import MCPARTICLES, TRACKER_COLLECTIONS, TRACKER_RELATIONS

class SlcioToHitsDataFrame:

    def __init__(self, slcio_file_paths):
        self.slcio_file_paths = slcio_file_paths


    def convert(self) -> pd.DataFrame:
        df = self.convert_all_files()
        df = self.postprocess_dataframe(df)
        df = self.sort_dataframe(df)
        return df


    def convert_all_files(self) -> pd.DataFrame:
        with mp.Pool(processes=mp.cpu_count()) as pool:
            all_hits_dfs = pool.map(self.convert_one_file, self.slcio_file_paths)
        print("Merging DataFrames ...")
        return pd.concat(all_hits_dfs, ignore_index=True)


    def convert_one_file(self, slcio_file_path: str) -> pd.DataFrame:
        print(f"Converting slcio file to DataFrame: {slcio_file_path}")

        # # preamble: cellid decoding


        # open the SLCIO file
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(slcio_file_path)

        # list for holding all hits
        rows = []

        # loop over all events in the slcio file
        for i_event, event in enumerate(reader):

            # preamble: cellid decoding
            if i_event == 0:
                for collection in TRACKER_COLLECTIONS:
                    col = event.getCollection(collection)
                    enc = col.getParameters().getStringVal(pyLCIO.EVENT.LCIO.CellIDEncoding)
                    print(f"CellID encoding for {collection}: {enc}")

            # get mcparticle info
            mcparticles = list(event.getCollection(MCPARTICLES))
            sim_px = [mcp.getMomentum()[0] for mcp in mcparticles]
            sim_py = [mcp.getMomentum()[1] for mcp in mcparticles]
            sim_pz = [mcp.getMomentum()[2] for mcp in mcparticles]
            sim_m = [mcp.getMass() for mcp in mcparticles]

            # inspect all tracking detectors
            for collection in TRACKER_RELATIONS:

                # get the relations collection
                rels = event.getCollection(collection)

                # for each relation, get the MC parent and the hit
                for rel in rels:
                    hit, sim_hit = rel.getFrom(), rel.getTo()
                    if not hit:
                        continue
                    if not sim_hit:
                        continue
                    mcp = sim_hit.getMCParticle()
                    if not mcp:
                        continue
                    if not mcp in mcparticles:
                        continue
                    i_sim = mcparticles.index(mcp)
                    rows.append({
                        'file': os.path.basename(slcio_file_path),
                        'i_event': i_event,
                        'i_sim': i_sim,
                        'sim_px': sim_px[i_sim],
                        'sim_py': sim_py[i_sim],
                        'sim_pz': sim_pz[i_sim],
                        'sim_m': sim_m[i_sim],
                        'hit_x': hit.getPosition()[0],
                        'hit_y': hit.getPosition()[1],
                        'hit_z': hit.getPosition()[2],
                        'hit_cellid0': hit.getCellID0(),
                        'hit_cellid1': hit.getCellID1(),
                    })

        # Close the reader
        reader.close()

        # Convert the list of hits to a pandas DataFrame
        print("Converting hits to DataFrame ...")
        return pd.DataFrame(rows)


    def postprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Postprocessing DataFrame ...")
        df['sim_p'] = np.sqrt(df['sim_px']**2 + df['sim_py']**2 + df['sim_pz']**2)
        df['sim_pt'] = np.sqrt(df['sim_px']**2 + df['sim_py']**2)
        df['sim_theta'] = np.arctan2(df['sim_pt'], df['sim_pz'])
        df['sim_eta'] = -np.log(np.tan(df['sim_theta'] / 2))
        df['sim_phi'] = np.arctan2(df['sim_py'], df['sim_px'])
        df['hit_R'] = np.sqrt(df['hit_x']**2 + df['hit_y']**2 + df['hit_z']**2)
        df['hit_system'] = np.right_shift(df['hit_cellid0'], 0) & 0b1_1111
        df['hit_side'] = np.right_shift(df['hit_cellid0'], 5) & 0b11
        df['hit_layer'] = np.right_shift(df['hit_cellid0'], 7) & 0b11_1111
        df['hit_module'] = np.right_shift(df['hit_cellid0'], 13) & 0b111_1111_1111
        df['hit_sensor'] = np.right_shift(df['hit_cellid0'], 24) & 0b1111_1111

        # remove redundant columns
        df = df.drop(columns=['hit_cellid0', 'hit_cellid1', 'sim_p', 'sim_px', 'sim_py'])

        # sort columns alphabetically
        return df[sorted(df.columns)]


    def sort_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Sorting DataFrame ...")
        df = df.sort_values(by=['file', 'i_event', 'i_sim', 'hit_R']).reset_index(drop=True)
        return df
