source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2025-01-28
k4run pythia.py -n 100 --Dumper.Filename events.hepmc --Pythia8.PythiaInterface.pythiacard p8_mumu_tt_ecm_10000.cmd
