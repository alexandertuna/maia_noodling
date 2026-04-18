import sys
import pyLCIO

FNAME = sys.argv[1] # "ttbar_reco_0.slcio"
# FNAME = "latest_image/ttbar_sim_0.slcio"
# FNAME = "latest_image/ttbar_sim_0_enableDetailedHitsAndParticleInfo.slcio"
print(f"File {FNAME}")

def main():

    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(FNAME)

    for i_event, event in enumerate(reader):
        print(f"Event {i_event}")
        if i_event == 0:
            for collection_name in event.getCollectionNames():
                n_col = event.getCollection(collection_name).getNumberOfElements()
                print(f"  Collection: {collection_name}, number of elements: {n_col}")


if __name__ == "__main__":
    main()
