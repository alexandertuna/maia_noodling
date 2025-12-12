import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams
rcParams.update({"font.size": 16})

class Plotter:


    def __init__(self, df: pd.DataFrame, pdf: str):
        self.df = df
        self.pdf = pdf


    def plot(self):
        with PdfPages(self.pdf) as pdf:
            self.plot_sim_pt(pdf)


    def plot_sim_pt(self, pdf: PdfPages):
        mask = ~(self.df["hit"].astype(bool))
        bins = 100
        fig, ax = plt.subplots(figsize=(8,8))
        ax.hist(self.df[mask]["sim_pt"],
                bins=bins,
                histtype="stepfilled",
                color="blue",
                alpha=0.5,
                label="All hits",
                )
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.set_xlabel("Simulated $p_T$ [GeV/c]")
        ax.set_ylabel("Counts")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.09)
        pdf.savefig()
        plt.close()
