#
# apptainer run -B /cvmfs/sw.hsf.org/key4hep/ /cvmfs/unpacked.cern.ch/ghcr.io/muoncollidersoft/mucoll-sim-alma9\:v2.9.8-amd64
# source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2025-01-28
#

time k4run pythia.py --Dumper.Filename ttbar.hepmc --Pythia8.PythiaInterface.pythiacard p8_mumu_tt_ecm10000.cmd

