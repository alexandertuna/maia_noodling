"""
CellID encoding for IBTrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
CellID encoding for IETrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
CellID encoding for OBTrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
CellID encoding for OETrackerHits: system:5,side:-2,layer:6,module:11,sensor:8
"""

import numpy as np
import pandas as pd
import os
import multiprocessing as mp

from constants import MCPARTICLES, SPEED_OF_LIGHT, MUON
from constants import MINIMUM_TIME, MAXIMUM_TIME

try:
    import pyLCIO
except ImportError as e:
    print("pyLCIO is not installed. Will continue onward and see what happens ...")

class SlcioToHitsDataFrame:

    def __init__(self, slcio_file_paths, collections, layers, sensors, signal):
        self.slcio_file_paths = slcio_file_paths
        self.collections = collections
        self.layers = layers
        self.sensors = sensors
        self.signal = signal


    def convert(self) -> pd.DataFrame:
        df = self.convert_all_files()
        df = self.postprocess_dataframe(df)
        df = self.filter_dataframe(df)
        return df


    def convert_all_files(self) -> pd.DataFrame:
        with mp.Pool(processes=mp.cpu_count()) as pool:
            all_hits_dfs = pool.map(self.convert_one_file, self.slcio_file_paths)
        print("Merging DataFrames ...")
        return pd.concat(all_hits_dfs, ignore_index=True)


    def convert_one_file(self, slcio_file_path: str) -> pd.DataFrame:
        print(f"Converting slcio file to DataFrame: {slcio_file_path}")

        # preamble: cellid decoding
        is_digi = "_digi_" in slcio_file_path
        is_sim = "_sim_" in slcio_file_path
        if not is_digi and not is_sim:
            raise ValueError(f"Cannot determine if file is digi or sim: {slcio_file_path}")

        # open the SLCIO file
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(slcio_file_path)

        # list for holding all hits
        rows = []

        # loop over all events in the slcio file
        for i_event, event in enumerate(reader):

            # get mcparticle info
            if self.signal:
                mcparticles = list(event.getCollection(MCPARTICLES))
                sim_px = [mcp.getMomentum()[0] for mcp in mcparticles]
                sim_py = [mcp.getMomentum()[1] for mcp in mcparticles]
                sim_pz = [mcp.getMomentum()[2] for mcp in mcparticles]
                sim_m = [mcp.getMass() for mcp in mcparticles]
                sim_q = [mcp.getCharge() for mcp in mcparticles]
                sim_pdg = [mcp.getPDG() for mcp in mcparticles]

            # inspect tracking detector collections
            for collection in self.collections:

                col = event.getCollection(collection)

                for obj in col:

                    # find the hit and the parent mc particle
                    hit, mcp = None, None
                    if is_digi:
                        # `obj` is a relation
                        hit, sim_hit = obj.getFrom(), obj.getTo()
                        if self.signal:
                            if not sim_hit:
                                continue
                            mcp = sim_hit.getMCParticle()
                    if is_sim:
                        # `obj` is a sim hit
                        hit = obj
                        if self.signal:
                            mcp = hit.getMCParticle()

                    # skip if hit or mcp is missing
                    if not hit:
                        continue
                    if self.signal and not mcp:
                        continue
                    if self.signal and not mcp in mcparticles:
                        continue
                    i_sim = mcparticles.index(mcp) if self.signal else -1
                    if self.signal and abs(sim_pdg[i_sim]) != MUON:
                        continue

                    # skip if trying to speed up
                    if self.layers and (np.right_shift(hit.getCellID0(), 7) & 0b11_1111) not in self.layers:
                        continue
                    if self.sensors and (np.right_shift(hit.getCellID0(), 24) & 0b1111_1111) not in self.sensors:
                        continue

                    # record the hit info
                    rows.append({
                        'file': os.path.basename(slcio_file_path),
                        'i_event': i_event,
                        'i_sim': i_sim,
                        'sim_px': sim_px[i_sim] if self.signal else 0,
                        'sim_py': sim_py[i_sim] if self.signal else 0,
                        'sim_pz': sim_pz[i_sim] if self.signal else 0,
                        'sim_m': sim_m[i_sim] if self.signal else 0,
                        'sim_q': sim_q[i_sim] if self.signal else 0,
                        'sim_pdg': sim_pdg[i_sim] if self.signal else 0,
                        'hit_x': hit.getPosition()[0],
                        'hit_y': hit.getPosition()[1],
                        'hit_z': hit.getPosition()[2],
                        'hit_e': hit.getEDep(),
                        'hit_t': hit.getTime(),
                        'hit_quality': hit.getQuality(),
                        'hit_cellid0': hit.getCellID0(),
                        'hit_cellid1': hit.getCellID1(),
                        'hit_is_digi': is_digi,
                        'hit_is_signal': self.signal,
                    })

        # Close the reader
        reader.close()

        # Convert the list of hits to a pandas DataFrame
        print("Converting hits to DataFrame ...")
        return pd.DataFrame(rows)


    def postprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Postprocessing DataFrame ...")
        print("df", df)
        # df['sim_p'] = np.sqrt(df['sim_px']**2 + df['sim_py']**2 + df['sim_pz']**2)
        df['sim_pt'] = np.sqrt(df['sim_px']**2 + df['sim_py']**2)
        df['sim_theta'] = np.arctan2(df['sim_pt'], df['sim_pz'])
        df['sim_eta'] = -np.log(np.tan(df['sim_theta'] / 2))
        df['sim_phi'] = np.arctan2(df['sim_py'], df['sim_px'])
        df['hit_r'] = np.sqrt(df['hit_x']**2 + df['hit_y']**2)
        df['hit_R'] = np.sqrt(df['hit_x']**2 + df['hit_y']**2 + df['hit_z']**2)
        df['hit_t_corrected'] = df['hit_t'] - (df['hit_R'] / SPEED_OF_LIGHT * ~df['hit_is_digi'])
        df['hit_system'] = np.right_shift(df['hit_cellid0'], 0) & 0b1_1111
        df['hit_side'] = np.right_shift(df['hit_cellid0'], 5) & 0b11
        df['hit_layer'] = np.right_shift(df['hit_cellid0'], 7) & 0b11_1111
        df['hit_module'] = np.right_shift(df['hit_cellid0'], 13) & 0b111_1111_1111
        df['hit_sensor'] = np.right_shift(df['hit_cellid0'], 24) & 0b1111_1111
        df['hit_theta'] = np.arctan2(df['hit_r'], df['hit_z'])
        df['hit_phi'] = np.arctan2(df['hit_y'], df['hit_x'])

        # remove redundant columns
        df = df.drop(columns=[
            'hit_cellid0',
            'hit_cellid1',
        ])

        # sort columns alphabetically
        return df[sorted(df.columns)]


    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Filtering DataFrame ...")
        subset = (df["hit_t_corrected"] >= MINIMUM_TIME) & \
                 (df["hit_t_corrected"] <= MAXIMUM_TIME)
        df = df[subset]
        return df

