#
# apptainer run -B /cvmfs/sw.hsf.org/key4hep/ /cvmfs/unpacked.cern.ch/ghcr.io/muoncollidersoft/mucoll-sim-alma9\:v2.9.8-amd64
# source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2025-01-28
#
# $ for IT in $(seq 10000 10999); do cp -a p8_mumu_tt_ecm10000.cmd cards/p8_mumu_tt_ecm10000_${IT}.cmd; sed -i "s/12345/${IT}/g" cards/p8_mumu_tt_ecm10000_${IT}.cmd; done
#

# for IT in $(seq 100 199); do
#     NEV="100" && \
#     time k4run pythia.py -n ${NEV} --Dumper.Filename ttbar_${NEV}ev_${IT}.hepmc --Pythia8.PythiaInterface.pythiacard p8_mumu_tt_ecm10000_${IT}.cmd
# done

time k4run pythia.py --Dumper.Filename ttbar.hepmc --Pythia8.PythiaInterface.pythiacard p8_mumu_tt_ecm10000.cmd

