NEV="1000" && \
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2025-01-28 && \
time k4run pythia.py -n ${NEV} --Dumper.Filename events_${NEV}.hepmc --Pythia8.PythiaInterface.pythiacard p8_mumu_tt_ecm10000.cmd
