import pyLCIO
import pandas as pd
from tqdm import tqdm
import multiprocessing as mp

from constants import MCPARTICLES, TRACKER_RELATIONS

class SlcioToHitsDataFrame:

    def __init__(self, slcio_file_paths):
        self.slcio_file_paths = slcio_file_paths


    def convert(self):
        # process files in parallel
        with mp.Pool(processes=mp.cpu_count()) as pool:
            all_hits_dfs = pool.map(self.convert_one_file, self.slcio_file_paths)
        return pd.concat(all_hits_dfs, ignore_index=True)


    def convert_one_file(self, slcio_file_path):

        # Open the SLCIO file
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(slcio_file_path)

        rows = []
        hits_data = []

        # Loop over all events in the slcio file
        # for i, event in enumerate(tqdm(reader)):
        for i_event, event in enumerate(reader):

            if i_event > 100:
                break

            if i_event == 0:
                print(event.getCollectionNames())
                print("")

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

            # test_mcps = list(event.getCollection('MCParticle'))
            # test_hits = event.getCollection('IBTrackerHits')
            # test_rels = event.getCollection('IBTrackerHitsRelations')
            # test_sims = event.getCollection('InnerTrackerBarrelCollection')
            # # print(f"Number of hits: {len(test_hits)}")
            # # print(f"Number of relations: {len(test_rels)}")
            # # print(f"Number of sim hits: {len(test_sims)}")
            # # print(f"Number of MCParticles: {len(test_mcps)}")
            # # print("")
            # test_isin = {}
            # for rel in test_rels:
            #     # print("")
            #     # print(rel.getFrom())
            #     # print(rel.getTo())
            #     # print(rel.getTo().getMCParticle())
            #     mcp = rel.getTo().getMCParticle()
            #     isin = mcp in test_mcps
            #     index = test_mcps.index(mcp) if isin else -1
            #     test_isin[index] = test_isin.get(index, 0) + 1
            #     print(f"{isin=} {index=}")
            # for key in test_isin:
            #     print(f"{key}: {test_isin[key]}")
            # if len(test_hits) == len(test_sims):
            #     continue
            # print(f"{len(test_hits)=} {len(test_rels)=} {len(test_sims)=} {len(test_mcps)=}")

            # # Get the collection of hits (assuming collection name is 'IBTrackerHits')
            # hits_collection = event.getCollection('IBTrackerHits')
            # if hits_collection is None:
            #     continue

            # # Loop over all hits in the collection
            # for hit in hits_collection:
            #     hit_info = {
            #         'x': hit.getPosition()[0],
            #         'y': hit.getPosition()[1],
            #         'z': hit.getPosition()[2],
            #         'time': hit.getTime(),
            #         'cellID0': hit.getCellID0()
            #     }
            #     hits_data.append(hit_info)

        # Close the reader
        reader.close()

        # Convert the list of hits to a pandas DataFrame
        df = pd.DataFrame(rows)
        hits_df = pd.DataFrame(hits_data)
        return df # , hits_df

