#
# apptainer run -B /cvmfs/sw.hsf.org/key4hep/ /cvmfs/unpacked.cern.ch/ghcr.io/muoncollidersoft/mucoll-sim-alma9\:v2.9.8-amd64
# source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2025-01-28
#

for IT in $(seq 10000 10999); do
    time k4run pythia.py --Dumper.Filename hepmc/ttbar_${IT}.hepmc --Pythia8.PythiaInterface.pythiacard cards/p8_mumu_tt_ecm10000_${IT}.cmd
done

