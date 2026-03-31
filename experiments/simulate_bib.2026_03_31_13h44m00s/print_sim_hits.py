import argparse
import pyLCIO
import logging
logger = logging.getLogger(__name__)

TRACKER = "InnerTrackerBarrelCollection"


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    ops = options()

    # Open the slcio file
    logger.info(f"Opening file: {ops.input}")
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(ops.input)

    # For each event, print the number of sim hits in the tracker
    for i, event in enumerate(reader):
        col = event.getCollection(TRACKER)
        logger.info(f"Event {i}: {col.getNumberOfElements()} sim hits")


def options():
    parser = argparse.ArgumentParser(description="Print sim hits from a given slcio file.")
    parser.add_argument("-i", "--input", type=str, required=True,
                        help="Path to the input slcio file.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
