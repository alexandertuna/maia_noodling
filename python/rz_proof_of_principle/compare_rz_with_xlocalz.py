import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def main():
    x0 = 127.0
    x1 = 129.0
    ys = np.linspace(-15, 15, 101)
    zs = np.linspace(0, 30, 101)


    x0s = x0 * np.ones_like(ys)
    x1s = x1 * np.ones_like(ys)
    z0s = z0 * np.ones_like(ys)
    z1s = z1 * np.ones_like(ys)
    r0s = np.sqrt(x0s**2 + ys**2)
    r1s = np.sqrt(x1s**2 + ys**2)

    with PdfPages("compare_rz_with_xlocalz.pdf") as pdf:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.plot(z0s, r0s, label=f"x={x0} cm", color="blue")
        ax.plot(z1s, r1s, label=f"x={x1} cm", color="red")
        ax.set_xlabel("z (cm)")
        ax.set_ylabel("r (cm)")
        ax.set_title("R-Z representation of detector layers at fixed x positions")
        ax.legend()
        ax.grid()
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.plot(z0s, r0s, label=f"x={x0} cm", color="blue")
        ax.plot(x1s, x1s, label=f"x={x1} cm", color="red")
        ax.set_xlabel("z (cm)")
        ax.set_ylabel("x (cm)")
        ax.set_title("X-Z representation of detector layers at fixed x positions")
        ax.legend()
        ax.grid()
        pdf.savefig()
        plt.close()

if __name__ == "__main__":
    main()
