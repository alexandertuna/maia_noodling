This is a directory for making ttbar slcio files at a muon collider detector.

The process includes:

- Make copies of `p8_mumu_tt_ecm10000.cmd` with a different seed for each copy
- Run `pythia.py` to generate hepmc files of the ttbar process
- Run `sim_steer_GEN_CONDOR.py` to simulate the particles passing through the MAIA detector
- Run `steer_reco_ttbar.py` to digitize and reconstruct the sim hits of the previous step into digitized hits, tracks, clusters, and PFO

Steering files include:

- `p8_mumu_tt_ecm10000.cmd` with seed initially set to 12345
- `sim_steer_GEN_CONDOR.py`, located at https://github.com/madbaron/SteeringMacros/blob/master/Sim/sim_steer_GEN_CONDOR.py
- `MAIA_v0.xml`, located at https://github.com/alexandertuna/k4geo/blob/main/MuColl/MAIA/compact/MAIA_v0/MAIA_v0.xml
- `steer_reco_ttbar.py`
