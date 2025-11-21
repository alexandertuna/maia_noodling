MCPARTICLES = "MCParticle"

TRACKER_COLLECTIONS = [
    "IBTrackerHits",
    "IETrackerHits",
    "OBTrackerHits",
    "OETrackerHits",
]

TRACKER_BARREL_COLLECTIONS = [
    "IBTrackerHits",
    "OBTrackerHits",
]

TRACKER_RELATIONS = [
    "IBTrackerHitsRelations",
    "IETrackerHitsRelations",
    "OBTrackerHitsRelations",
    "OETrackerHitsRelations",
]

TRACKER_BARREL_RELATIONS = [
    "IBTrackerHitsRelations",
    "OBTrackerHitsRelations",
]

SIM_TRACKER_COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "InnerTrackerEndcapCollection",
    "OuterTrackerBarrelCollection",
    "OuterTrackerEndcapCollection",
]

SIM_TRACKER_BARREL_COLLECTIONS = [
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
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

SPEED_OF_LIGHT = 299.792458  # mm/ns

MINIMUM_PT = 1.0  # GeV

MINIMUM_HITS_PER_MODULE = 10
MINIMUM_FRACTION_PER_MODULE = 0.001
MINIMUM_TIME = -0.18 # ns
MAXIMUM_TIME = 0.3 # ns

InnerTracker_Barrel_DoubleLayer_Gap = 2.0 # mm
InnerTracker_Barrel_radius_0 = 127 # mm
InnerTracker_Barrel_radius_1 = 167 # mm
InnerTracker_Barrel_radius_2 = 510 # mm
InnerTracker_Barrel_radius_3 = 550 # mm

OuterTracker_Barrel_DoubleLayer_Gap = 6.0 # mm
OuterTracker_Barrel_radius_0 = 819 # mm
OuterTracker_Barrel_radius_1 = 899 # mm
OuterTracker_Barrel_radius_2 = 1366 # mm
OuterTracker_Barrel_radius_3 = 1446 # mm

INNER_TRACKER_BARREL_RADII = [
    InnerTracker_Barrel_radius_0,
    InnerTracker_Barrel_radius_0 + InnerTracker_Barrel_DoubleLayer_Gap,
    InnerTracker_Barrel_radius_1,
    InnerTracker_Barrel_radius_1 + InnerTracker_Barrel_DoubleLayer_Gap,
    InnerTracker_Barrel_radius_2,
    InnerTracker_Barrel_radius_2 + InnerTracker_Barrel_DoubleLayer_Gap,
    InnerTracker_Barrel_radius_3,
    InnerTracker_Barrel_radius_3 + InnerTracker_Barrel_DoubleLayer_Gap,
]

OUTER_TRACKER_BARREL_RADII = [
    OuterTracker_Barrel_radius_0,
    OuterTracker_Barrel_radius_0 + OuterTracker_Barrel_DoubleLayer_Gap,
    OuterTracker_Barrel_radius_1,
    OuterTracker_Barrel_radius_1 + OuterTracker_Barrel_DoubleLayer_Gap,
    OuterTracker_Barrel_radius_2,
    OuterTracker_Barrel_radius_2 + OuterTracker_Barrel_DoubleLayer_Gap,
    OuterTracker_Barrel_radius_3,
    OuterTracker_Barrel_radius_3 + OuterTracker_Barrel_DoubleLayer_Gap,
]

BARREL_RADII = {
    IT_BARREL: INNER_TRACKER_BARREL_RADII,
    OT_BARREL: OUTER_TRACKER_BARREL_RADII,
}
