"""
694 2025_10_08_15h19m46s
700 2025_10_08_15h20m46s
702 2025_10_08_15h21m46s
708 2025_10_08_15h22m46s
718 2025_10_08_15h23m46s
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({'font.size': 16})

FNAME = "/ceph/users/atuna/work/maia/maia_noodling/experiments/simulate_bib.2025_10_08_09h35m49s/progress.txt"
TOTAL = 6666 * 2

def main():
    data = pd.read_csv(FNAME, sep=" ", header=None, names=["id", "timestamp"])
    # data["timestamp"] = pd.to_datetime(data["timestamp"])
    print(data)
    with PdfPages("progress_condor_jobs.pdf") as pdf:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.plot(data["id"])
        ax.set_xlabel("Minutes since start")
        ax.set_ylabel("Number of completed Condor jobs")
        ax.set_ylim(0, TOTAL*1.05)
        ax.axhline(TOTAL, color="gray", linestyle="--")
        ax.grid()
        ax.tick_params(right=True, top=True, direction="in")
        fig.subplots_adjust(left=0.15, bottom=0.08, right=0.95, top=0.95)
        pdf.savefig()
        plt.close()

    # plt.plot(data["timestamp"], data["id"])
    # plt.xlabel("Time")
    # plt.ylabel("Job ID")
    # plt.title("Progress of Condor Jobs")
    # plt.show()

if __name__ == "__main__":
    main()
