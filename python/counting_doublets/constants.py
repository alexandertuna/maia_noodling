import numpy as np

MUON = 13
ANTIMUON = -MUON
MUON_NEUTRINO = 14
MUON_ANTINEUTRINO = -MUON_NEUTRINO
PARTICLES_OF_INTEREST = [
    MUON,
    MUON_NEUTRINO,
]

SPEED_OF_LIGHT = 299.792458  # mm/ns

SIGNAL = "muonGun"

ONE_MM = 1.0
ZERO_POINT_ZERO_ONE_MM = 0.01
ONE_GEV = 1.0
ONE_POINT_FIVE_GEV = 1.5

MM_TO_CM = 0.1
CM_TO_MM = 10.0
BYTE_TO_MB = 1e-6
MEV_TO_GEV = 1e-3

CODE = "/ceph/users/atuna/work/maia"
XML = f"{CODE}/k4geo/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml"


EPSILON = 1e-6
MCPARTICLE = "MCParticle"
MAGNETIC_FIELD = 5.0 # Tesla

BARREL_TRACKER_MAX_ETA = 0.65
BARREL_TRACKER_MAX_RADIUS = 1446.0

OUTSIDE_BOUNDS = 0
INSIDE_BOUNDS = 1
UNDEFINED_BOUNDS = 2
POSSIBLE_BOUNDS = [OUTSIDE_BOUNDS, INSIDE_BOUNDS, UNDEFINED_BOUNDS]
BOUNDS = {
    OUTSIDE_BOUNDS: "outside",
    INSIDE_BOUNDS: "inside",
    UNDEFINED_BOUNDS: "undefined",
}

MIN_COSTHETA = 0.0
MIN_SIMHIT_PT_FRACTION = 0.7
MAX_TIME = 3.0 # in ns

INNER_TRACKER_BARREL_COLLECTION = "InnerTrackerBarrelCollection"
OUTER_TRACKER_BARREL_COLLECTION = "OuterTrackerBarrelCollection"
COLLECTIONS = [
    # INNER_TRACKER_BARREL_COLLECTION,
    OUTER_TRACKER_BARREL_COLLECTION,
]
INNER_TRACKER_BARREL = 3
OUTER_TRACKER_BARREL = 5
SYSTEMS = [
    # INNER_TRACKER_BARREL,
    OUTER_TRACKER_BARREL,
]
LAYERS = [
    0,
    1,
    2,
    3,
    # 4,
    # 5,
    # 6,
    # 7,
]
DOUBLELAYERS = [
    0,
    1,
    # 2,
    # 3,
]
QUADLAYERS = [
    0,
]

DZ_CUT = np.array([
    22, # mm # doublelayer 0
    29, # mm # doublelayer 1
])
DR_CUT = np.array([
    260, # mm # doublelayer 0
    313, # mm # doublelayer 1
])
DETA_CUT = np.array([
    0.0023, # quadlayer 0
])
DPHI_CUT = np.array([
    0.034, # quadlayer 0
])
DDR_CUT = np.array([
    69.0, # quadlayer 0
])
DDZ_CUT = np.array([
    20.0, # quadlayer 0
])

REQ_PASSTHROUGH = "no cuts"
REQ_RZ = "rz req."
REQ_XY = "xy req."
REQ_RZ_XY = "both req."
DOUBLET_REQS = [
    REQ_PASSTHROUGH,
    REQ_XY,
    REQ_RZ,
    REQ_RZ_XY,
]
NICKNAMES = {
    INNER_TRACKER_BARREL: "ITB",
    OUTER_TRACKER_BARREL: "OTB",
}
