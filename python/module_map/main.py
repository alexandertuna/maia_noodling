import argparse
from slcio_to_hits_dataframe import SlcioToHitsDataFrame

# FNAME = "/ceph/users/atuna/work/maia/maia_noodling/samples/v00/muonGun_pT_0_10_nobib/muonGun_pT_0_10_digi_0.slcio"
FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_muonGun.2025_11_06_21h31m00s/muonGun_pT_0_10_digi_0.slcio"

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default=FNAME,
                        help="Comma-separated list of input slcio files")
    return parser.parse_args()


def main():
    ops = options()
    converter = SlcioToHitsDataFrame(ops.i.split(","))
    hits_df = converter.convert()
    print(hits_df)


if __name__ == "__main__":
    main()
