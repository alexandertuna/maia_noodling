MCPARTICLES = "MCParticle"

TRACKER_COLLECTIONS = [
    "IBTrackerHits",
    "IETrackerHits",
    "OBTrackerHits",
    "OETrackerHits",
]

TRACKER_RELATIONS = [
    "IBTrackerHitsRelations",
    "IETrackerHitsRelations",
    "OBTrackerHitsRelations",
    "OETrackerHitsRelations",
]

VXD_BARREL = 1
VXD_ENDCAP = 2
IT_BARREL = 3
IT_ENDCAP = 4
OT_BARREL = 5
OT_ENDCAP = 6

DET_IDS = [
    IT_BARREL,
    IT_ENDCAP,
    OT_BARREL,
    OT_ENDCAP,
]

DET_NAMES = {
    IT_BARREL: "IT Barrel",
    IT_ENDCAP: "IT Endcap",
    OT_BARREL: "OT Barrel",
    OT_ENDCAP: "OT Endcap",
}

MINIMUM_PT = 1.0  # GeV

MINIMUM_HITS_PER_MODULE = 10
MINIMUM_FRACTION_PER_MODULE = 0.001

