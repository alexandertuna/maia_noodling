import pyLCIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib import rcParams
rcParams.update({"font.size": 16})

COLNAMES = [
    "VertexBarrelCollection",
    "InnerTrackerBarrelCollection",
    "OuterTrackerBarrelCollection",
]
SPEED_OF_LIGHT = 299.792458  # mm/ns
EVENT = 8873
FNAME = "/ceph/users/atuna/work/maia/maia_noodling/samples/v00/muonGun_pT_0_10_nobib/muonGun_pT_0_10_digi_10.slcio"

def main():
    df = get_dataframe(FNAME)
    print(df)
    print(df["hit_t"].describe())
    with PdfPages(f"event_{EVENT}.pdf") as pdf:
        plot(df, pdf)
    plot_gif(df)
    plot_gif(df, cumulative=True)


def get_dataframe(fname: str) -> pd.DataFrame:
    reader = pyLCIO.IOIMPL.LCFactory.getInstance().createLCReader()
    reader.open(fname)

    hits = []

    for i_event, event in enumerate(reader):
        if not i_event in [EVENT]:
            continue

        print(f"Processing event {i_event}")
        for name in sorted(list(event.getCollectionNames())):
            print(name)
        for colname in COLNAMES:
            collection = event.getCollection(colname)
            print(f"Collection: {colname}, Number of elements: {len(collection)}")
            for hit in collection:
                hits.append({
                    "event": i_event,
                    "collection": colname,
                    "hit_x": hit.getPosition()[0],
                    "hit_y": hit.getPosition()[1],
                    "hit_z": hit.getPosition()[2],
                    "hit_t": hit.getTime(),
                })

    df = pd.DataFrame(hits)
    df['hit_r'] = np.sqrt(df['hit_x']**2 + df['hit_y']**2)
    df['hit_R'] = np.sqrt(df['hit_x']**2 + df['hit_y']**2 + df['hit_z']**2)
    df['hit_t_corrected'] = df['hit_t'] - (df['hit_R'] / SPEED_OF_LIGHT)
    return df

def plot(df: pd.DataFrame, pdf: PdfPages):
    plot_time(df, pdf)
    plot_position(df, pdf)
    plot_position_in_time_slices(df, pdf)


def plot_time(df: pd.DataFrame, pdf: PdfPages):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.hist(df["hit_t"], bins=100)
    ax.set_xlabel("Hit time (ns)")
    ax.set_ylabel("Counts")
    pdf.savefig()
    plt.close()

def plot_position(df: pd.DataFrame, pdf: PdfPages):
    # rz
    fig, ax = plt.subplots(figsize=(8,8))
    sc = ax.scatter(df["hit_z"], df["hit_r"],
                    c=df["hit_t"], cmap='gist_heat', s=1)
    ax.set_xlabel("Hit z (mm)")
    ax.set_ylabel("Hit r (mm)")
    plt.colorbar(sc, ax=ax, label="Hit time (ns)")
    pdf.savefig()
    plt.close()

    # xy
    fig, ax = plt.subplots(figsize=(8,8))
    sc = ax.scatter(df["hit_x"], df["hit_y"],
                    c=df["hit_t"], cmap='gist_heat', s=1)
    ax.set_xlabel("Hit x (mm)")
    ax.set_ylabel("Hit y (mm)")
    ax.set_xlim([-1490, 1490])
    ax.set_ylim([-1490, 1490])
    plt.colorbar(sc, ax=ax, label="Hit time (ns)")
    fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
    pdf.savefig()
    plt.close()


def plot_position_in_time_slices(df: pd.DataFrame, pdf: PdfPages):
    slices = [
        (0, 10),
        (10, 20),
        (20, 30),
        (30, 40),
        (40, 50),
        (50, 60),
        (60, 70),
        (70, 80),
        (80, 90),
        (90, 100),
        (100, 110),
        (110, 120),
        (120, 130),
        (130, 140),
        (140, 150),
        (150, 160),
        (160, 170),
        (170, 180),
        (180, 190),
        (190, 200),
        (200, 210),
    ]
    for (tmin, tmax) in slices:
        subset = df[(df["hit_t"] >= tmin) & (df["hit_t"] < tmax)]
        fig, ax = plt.subplots(figsize=(8,8))
        sc = ax.scatter(subset["hit_x"], subset["hit_y"], c="black", s=10)
        ax.set_xlabel("Hit x (mm)")
        ax.set_ylabel("Hit y (mm)")
        ax.set_title(f"Hits time in [{tmin}, {tmax}] ns")
        ax.set_xlim([-1490, 1490])
        ax.set_ylim([-1490, 1490])
        fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)
        pdf.savefig()
        plt.close()


def plot_gif(df: pd.DataFrame, cumulative: bool = False):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim([-1490, 1490])
    ax.set_ylim([-1490, 1490])
    ax.set_xlabel("Hit x (mm)")
    ax.set_ylabel("Hit y (mm)")
    ax.grid()
    circle_line, = ax.plot([], [], linestyle="--", color="red", zorder=1)
    scat = ax.scatter([], [], c="black", s=20, zorder=2)
    fig.subplots_adjust(left=0.15, right=0.95, top=0.94, bottom=0.1)

    def update(frame):
        tmin = frame * 10
        tmax = tmin + 10
        if cumulative:
            tmin = df["hit_t"].min()
        subset = df[(df["hit_t"] >= tmin) & (df["hit_t"] < tmax)]
        scat.set_offsets(subset[["hit_x", "hit_y"]].values)
        if len(subset) >= 3 and not cumulative:
            x = subset["hit_x"].to_numpy()
            y = subset["hit_y"].to_numpy()
            xc, yc, R = fit_circle(x, y)
            print(f"Fitted circle at t in [{tmin}, {tmax}] ns: center=({xc:.1f}, {yc:.1f}), R={R:.1f} mm")
            theta_plot = np.linspace(0, 2*np.pi, 400)
            cx = xc + R * np.cos(theta_plot)
            cy = yc + R * np.sin(theta_plot)
            circle_line.set_data(cx, cy)
        else:
            circle_line.set_data([], [])
        ax.set_title(f"Hits with time in [{tmin}, {tmax}] ns and fitted circle" if not cumulative else f"Hits time < {tmax} ns")
        ax.set_axisbelow(True)
        return circle_line, scat

    ani = FuncAnimation(fig, update, frames=21, blit=True)
    writer = PillowWriter(fps=5)
    tag = "cumulative" if cumulative else "sliced"
    ani.save(f"event_{EVENT}_{tag}.gif", writer=writer)
    plt.close()


def fit_circle(x, y):
    """
    Fit a circle in the least-squares sense to points (x, y).

    Returns:
        xc, yc, R  (center and radius)
    """
    x = np.asarray(x)
    y = np.asarray(y)

    # Build the system: [x y 1] [D E F]^T = -(x^2 + y^2)
    A = np.column_stack([x, y, np.ones_like(x)])
    b = -(x**2 + y**2)

    D, E, F = np.linalg.lstsq(A, b, rcond=None)[0]

    xc = -D / 2.0
    yc = -E / 2.0
    R = np.sqrt((D**2 + E**2) / 4.0 - F)

    return xc, yc, R


if __name__ == "__main__":
    main()
