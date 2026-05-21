"""
For each lcio file in this directory,
 for each event in the lcio file,
 print each collection name and the length of the collection.
 Do this alphabetically by collection name.
"""
import glob
import pyLCIO

def main():
    max_col_name_length = int(30)
    for lcio_file in sorted(glob.glob("*digi*.slcio")):
        print(f"File: {lcio_file}")
        reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
        reader.open(lcio_file)
        for event in reader:
            print(f"  Event: {event.getEventNumber()}")
            collection_names = sorted(event.getCollectionNames())
            for name in collection_names:
                collection = event.getCollection(name)
                print(f"    Collection: {str(name):{max_col_name_length}} {len(collection)}")
        reader.close()


if __name__ == "__main__":
    main()
