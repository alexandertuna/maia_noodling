import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib import rcParams
rcParams.update({
    "font.size": 16,
    "figure.figsize": (8, 8),
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "axes.grid": True,
    "axes.grid.which": "both",
    "axes.axisbelow": True,
    "grid.linewidth": 0.5,
    "grid.alpha": 0.1,
    "grid.color": "gray",
    "figure.subplot.left": 0.14,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

class Timelapse:

    def __init__(self, df: pd.DataFrame, event: int, gif: str):
        self.df = df
        self.event = event
        self.gif = gif
        self.cumulative = False
        self.make_gif()

    
    def make_gif(self):
        start_t = -5
        delta_t = 1 # ns
        fig, ax = plt.subplots(figsize=(8,8))
        ax.set_xlabel("Sim. hit z (mm)")
        ax.set_ylabel("Sim. hit r (mm)")
        ax.grid()
        hist2d = True

        if hist2d:
            bins = [
                np.linspace(-1600, 1600, 320),
                np.linspace(0, 1600, 320)
            ]
            cmin, vmax = 0.5, 50
            norm = Normalize(vmin=cmin, vmax=vmax)
            _, xedges, yedges, quad = ax.hist2d([], [], bins=bins, cmap="gist_rainbow", norm=norm)
            fig.colorbar(quad, ax=ax, pad=0.01, label="Sim. hits")
        else:
            ax.set_xlim([-1600, 1600])
            ax.set_ylim([0, 1600])
            scat = ax.scatter([], [])

        def update(frame):
            tmin = start_t + frame
            tmax = tmin + delta_t
            ax.set_title(f"Hits with time in [{tmin}, {tmax}] ns")
            ax.set_axisbelow(True)
            subset = self.df[(self.df["simhit_t"] >= tmin) & (self.df["simhit_t"] < tmax)]
            if hist2d:
                x = subset["simhit_z"].to_numpy()
                y = subset["simhit_r"].to_numpy()
                H, _, _ = np.histogram2d(x, y, bins=[xedges, yedges])
                H_masked = np.ma.masked_less(H, cmin)
                if frame == 10:
                    print("H:")
                    print(H)
                    print("H ma:")
                    print(np.ma.masked_less(H, cmin))
                quad.set_array(H_masked.T.ravel())
                # optional: keep colors sensible as occupancy changes
                # quad.set_clim(vmin=0, vmax=max(1, H.max()))
                return (quad,)
            else:
                scat.set_offsets(subset[["simhit_z", "simhit_r"]].values)
                return (scat, )

        ani = FuncAnimation(fig, update, frames=26, blit=True)
        writer = PillowWriter(fps=5)
        ani.save(self.gif, writer=writer)
        plt.close()        