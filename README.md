# maia_noodling

## Relevant repositories

- https://github.com/alexandertuna/k4geo/
  - For the edited MAIA geometry
- https://github.com/madbaron/SteeringMacros
  - For sim, digi, and reco settings
- https://github.com/madbaron/detector-simulation
  - For scripts related to BIB processing
  - Formerly for the MAIA geometry
- https://github.com/MuonColliderSoft/mucoll-benchmarks/
  - For particle gun event generation
- https://github.com/madbaron/myMuCutils/
  - For inspiration about batch processing data
- https://github.com/madbaron/MyBIBUtils
  - For BIB classes which we don't really use

## Notes on where I go AWOL relative to baseline MAIA

- `k4geo`
  - Doublet geometry in the barrel tracker:
  - `MuColl/MAIA/compact/MAIA_v0/InnerTracker_o2_v06_01.xml`
  - `MuColl/MAIA/compact/MAIA_v0/OuterTracker_o2_v06_01.xml`
- `SteeringMacros/PandoraSettings/PandoraSettingsDefault.xml`
  - Change `<HistogramFile>` path to match my filesystem
- `SteeringMacros/k4Reco/steer_reco.py`:
  - Remove tracker endcap sim hits, tracker barrel digi hits, and tracker endcap digi hits from output
  - Relax OverlayMIX integration times from `-0.36, 0.36` to `-5.0, 15.0`
  - https://github.com/alexandertuna/SteeringMacros/tree/ShrinkOutputSize

## Notes on BIB sample productions

- simulate_bib.2026_01_07_22h00m00s
  - Geo: https://github.com/alexandertuna/k4geo/tree/KITP_10TeV_ITOT_doublets_v01/
  - Decrease OT doublet spacing from 6mm to 2mm, which is the same as IT
  - Increase OT sensor size from 30mm,30mm to 60mm,60mm
  - 100% BIB, no incoherent ee pairs
- simulate_bib.2025_10_17_10h40m00s
  - Geo: https://github.com/alexandertuna/k4geo/tree/KITP_10TeV_ITOT_doublets
  - Remake BIB after fixing bug in z-momentum of detector-simulation/utils/fluka_remix.py
  - Bug: Alex forgot to update the path for pruning away MCParticles. Bad production
- simulate_bib.2025_10_08_09h35m49s
  - Geo: https://github.com/alexandertuna/k4geo/tree/KITP_10TeV_ITOT_doublets
  - First attempt at BIB production with modified MAIA geometry
  - 100% BIB, no incoherent ee pairs

