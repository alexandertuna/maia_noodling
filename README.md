# maia_noodling

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

