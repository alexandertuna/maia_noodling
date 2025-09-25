import sys
import pyLCIO

fname = sys.argv[1]
print(fname)

n = 1
reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
reader.open(fname)
for i_event, event in enumerate(reader):
    if i_event >= n:
        break
    print(i_event, event.getCollectionNames())

