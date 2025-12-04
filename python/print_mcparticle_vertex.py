import argparse
import pyLCIO

def main():
    ops = options()
    if not ops.i:
        raise ValueError("Input LCIO file must be specified with -i option.")
    if not ops.n:
        raise ValueError("Number of events to process must be specified with -n option.")

    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(ops.i)

    # loop over all events in the slcio file
    for i_event, event in enumerate(reader):

        if i_event >= ops.n:
            break

        for name in event.getCollectionNames():
            print(name)

        mcps = list(event.getCollection("MCParticle"))
        for mcp in mcps:
            pdg = mcp.getPDG()
            vertex = mcp.getVertex()
            vx, vy, vz = vertex[0], vertex[1], vertex[2]
            print(f"Event {i_event} MCParticle PDG: {pdg:3}, Vertex: ({vx:9.3f}, {vy:9.3f}, {vz:9.3f})")



def options():
    parser = argparse.ArgumentParser(description="Print MCParticle vertex information from an LCIO file.")
    parser.add_argument("-i", type=str, help="Input LCIO file")
    parser.add_argument("-n", type=int, help="Number of events to process")
    return parser.parse_args()


if __name__ == "__main__":
    main()
