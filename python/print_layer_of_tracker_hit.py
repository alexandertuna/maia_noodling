import pyLCIO
from pyLCIO import EVENT

fname = "muonGun_pT_0_10_digi_0.slcio"
tracker = "InnerTrackerBarrelCollection"
nevents = 4

reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
reader.open(fname)
for i_event, event in enumerate(reader):
    if i_event >= nevents:
        break
    col = event.getCollection(tracker)
    enc = col.getParameters().getStringVal(EVENT.LCIO.CellIDEncoding)
    if i_event == 0:
        print(f"CellID encoding for {tracker}\n{enc}")
    for i_hit, hit in enumerate(col):
        cellid0, cellid1 = hit.getCellID0(), hit.getCellID1()
        system = ((cellid0 >> 0) & 0x1f)
        layer = ((cellid0 >> 7) & 0x3f)
        x, y, z = hit.getPositionVec().X(), hit.getPositionVec().Y(), hit.getPositionVec().Z()
        print(f"Event {i_event}, hit {i_hit}: cellID0 = {cellid0:08x}, system = {system}, layer = {layer}, xyz = ({x:8.3f}, {y:8.3f}, {z:8.3f})")

