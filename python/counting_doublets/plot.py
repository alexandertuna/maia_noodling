import inspect
import textwrap
import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.backends.backend_pdf import PdfPages
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
    # "axes.axisbelow": True,
    "grid.linewidth": 0.5,
    "grid.alpha": 0.1,
    "grid.color": "gray",
    "figure.subplot.left": 0.15,
    "figure.subplot.bottom": 0.09,
    "figure.subplot.right": 0.97,
    "figure.subplot.top": 0.95,
})

from constants import MUON, ANTIMUON
from constants import BARREL_TRACKER_MAX_ETA
from constants import BARREL_TRACKER_MAX_RADIUS
from constants import ONE_POINT_FIVE_GEV, ONE_MM, ZERO_POINT_ZERO_ONE_MM
from constants import NICKNAMES, OUTER_TRACKER_BARREL
from constants import DZ_CUT, DR_CUT
from constants import REQ_PASSTHROUGH, REQ_RZ, REQ_XY, REQ_RZ_XY
from constants import DOUBLET_REQS
from constants import MIN_COSTHETA, MIN_SIMHIT_PT_FRACTION, MAX_TIME


class Plotter:

    def __init__(
        self,
        signal: bool,
        mcps: pd.DataFrame,
        simhits: pd.DataFrame,
        doublets: pd.DataFrame,
        linesegments: pd.DataFrame,
        pdf: str,
    ):
        self.signal = signal
        self.mcps = mcps
        self.simhits = simhits
        self.doublets = doublets
        self.linesegments = linesegments
        self.pdf = pdf
        if self.signal:
            self.add_simhit_mcp_features()
            self.add_doublet_mcp_features()
            self.add_linesegment_mcp_features()


    def plot(self):
        logger.info(f"Writing plots to {self.pdf} ...")
        with PdfPages(self.pdf) as pdf:
            self.plot_numbers_for_comparison(pdf)
            self.plot_time(pdf)
            # self.plot_layer_occupancy_1d(pdf)
            # self.plot_layer_occupancy_2d(pdf)
            # self.plot_radius_vs_layer(pdf)
            # self.plot_doublet_occupancy(pdf)
            # self.plot_doublet_features(pdf)
            self.plot_linesegment_features(pdf)
            if self.signal:
                self.write_denominator_info(pdf)
                # self.plot_doublet_efficiency_vs_kinematics(pdf)
                # self.write_doublet_denominator_info(pdf)
                # self.plot_doublet_quality_efficiency(pdf)


    def plot_numbers_for_comparison(self, pdf: PdfPages):
        """
        Cutflow comparison!
        """
        if self.signal:
            self.plot_numbers_for_comparison_signal(pdf)
        else:
            self.plot_numbers_for_comparison_background(pdf)


    def plot_numbers_for_comparison_signal(self, pdf: PdfPages):

        # part 1: simhits
        mask = np.ones(len(self.simhits), dtype=bool)
        for [req, label] in [
            [self.simhits["simhit_layer"].isin([0, 1]), "All simhits in layers 0 and 1"],
            [np.abs(self.simhits["mcp_pdg"]) == MUON, "abs(pdg) == muon"],
            [self.simhits["mcp_q"] != 0, "q is not 0"],
            [self.simhits["mcp_pt"] > ONE_POINT_FIVE_GEV, "pT > 1.5 GeV"],
            [np.abs(self.simhits["mcp_eta"]) < BARREL_TRACKER_MAX_ETA, f"abs(eta) < {BARREL_TRACKER_MAX_ETA}"],
            [self.simhits["mcp_vertex_r"] < ZERO_POINT_ZERO_ONE_MM, "vertex r < 0.01 mm"],
            [np.abs(self.simhits["mcp_vertex_z"]) < ZERO_POINT_ZERO_ONE_MM, "abs(vertex z) < 0.01 mm"],
            [self.simhits["simhit_t_corrected"] < MAX_TIME, f"corrected t < {MAX_TIME} ns"],
            [self.simhits["simhit_costheta"] > MIN_COSTHETA, f"costheta > {MIN_COSTHETA}"],
            [self.simhits["simhit_p"] / self.simhits["mcp_p"] > MIN_SIMHIT_PT_FRACTION, f"simhit p / mcp p > {MIN_SIMHIT_PT_FRACTION}"],
            # [self.simhits["simhit_sensor"] == 20, "z-sensor 20"],
            # [self.simhits["simhit_module"] == 0, "phi-module 0"],
        ]:
            mask &= req
            logger.info(f"* {label:<30} :: {mask.sum():>10}")

        # part 2a: doublets by hand
        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_module", # the phi-module
            "simhit_sensor", # the z-sensor
        ]
        lower_mask = mask & (self.simhits["simhit_layer_mod_2"] == 0)
        upper_mask = mask & (self.simhits["simhit_layer_mod_2"] == 1)
        logger.info(f"* {'Lower hit':<30} :: {lower_mask.sum():>10}")
        logger.info(f"* {'Upper hit':<30} :: {upper_mask.sum():>10}")

        # logger.info("Getting lower and upper hits ...")
        lower = self.simhits[lower_mask].rename(columns={"i_mcp": "i_mcp_lower"})[doublet_cols + ["i_mcp_lower"]]
        upper = self.simhits[upper_mask].rename(columns={"i_mcp": "i_mcp_upper"})[doublet_cols + ["i_mcp_upper"]]
        doublets = lower.merge(upper, on=doublet_cols, how="inner")
        logger.info(f"* {'Doublets':<30} :: {len(doublets):>10}")

        same_mcp = doublets["i_mcp_lower"] == doublets["i_mcp_upper"]
        logger.info(f"* {'Doublets from same MCP':<30} :: {same_mcp.sum():>10}")

        # part 2b: doublets with dr and dz cuts
        doublelayer = self.doublets["simhit_layer_div_2"]
        dl_0 = doublelayer == 0
        dl_1 = doublelayer == 1
        baseline_cuts = (
            (self.doublets["i_mcp"] >= 0) &
            (np.abs(self.doublets["mcp_pdg"]) == MUON) &
            (self.doublets["mcp_q"] != 0) &
            (self.doublets["mcp_pt"] > ONE_POINT_FIVE_GEV) &
            (np.abs(self.doublets["mcp_eta"]) < BARREL_TRACKER_MAX_ETA) &
            (self.doublets["mcp_vertex_r"] < ZERO_POINT_ZERO_ONE_MM) &
            (np.abs(self.doublets["mcp_vertex_z"]) < ZERO_POINT_ZERO_ONE_MM) &
            (self.doublets["simhit_t_corrected_lower"] < MAX_TIME) &
            (self.doublets["simhit_t_corrected_upper"] < MAX_TIME) &
            (self.doublets["simhit_costheta_lower"] > MIN_COSTHETA) &
            (self.doublets["simhit_costheta_upper"] > MIN_COSTHETA) &
            (self.doublets["simhit_p_lower"] / self.doublets["mcp_p"] > MIN_SIMHIT_PT_FRACTION) &
            (self.doublets["simhit_p_upper"] / self.doublets["mcp_p"] > MIN_SIMHIT_PT_FRACTION)
        )
        quality_cuts = (
            (np.abs(self.doublets["doublet_dz"]) < DZ_CUT[doublelayer]) &
            (np.abs(self.doublets["doublet_dr"]) < DR_CUT[doublelayer]) &
            baseline_cuts
        )
        doublets_0 = self.doublets[baseline_cuts & dl_0]
        doublets_1 = self.doublets[baseline_cuts & dl_1]
        logger.info(f"* {'Doublets, baseline, L01':<30} :: {len(doublets_0):>10}")
        logger.info(f"* {'Doublets, baseline, L23':<30} :: {len(doublets_1):>10}")
        doublets_0 = self.doublets[quality_cuts & dl_0]
        doublets_1 = self.doublets[quality_cuts & dl_1]
        logger.info(f"* {'Doublets, drdz cuts, L01':<30} :: {len(doublets_0):>10}")
        logger.info(f"* {'Doublets, drdz cuts, L23':<30} :: {len(doublets_1):>10}")

        # part 3: line segments
        keys = [
            "file",
            "i_event",
            "i_mcp",
        ]
        segments = doublets_0.merge(
            doublets_1,
            on=keys,
            how="inner",
            validate="many_to_many",
            suffixes=("_lower", "_upper"),
        )
        logger.info(f"* {'Line segments from doublets':<30} :: {len(segments):>10}")


    def plot_numbers_for_comparison_background(self, pdf: PdfPages):
        layers = [0, 1]
        the_doublelayer = layers[0] // 2

        # part 1: simhits
        mask = np.ones(len(self.simhits), dtype=bool)
        for [req, label] in [
            [self.simhits["simhit_layer"].isin(layers), f"All simhits in layers {layers}"],
            # [self.simhits["simhit_sensor"] == 20, "z-sensor 20"],
            # [self.simhits["simhit_module"] == 0, "phi-module 0"],
        ]:
            mask &= req
            logger.info(f"* {label:<30} :: {mask.sum():>10}")

        # part 2: doublets
        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_module", # the phi-module
            "simhit_sensor", # the z-sensor
        ]
        lower_mask = mask & (self.simhits["simhit_layer_mod_2"] == 0)
        upper_mask = mask & (self.simhits["simhit_layer_mod_2"] == 1)
        logger.info(f"* {'Lower hit':<30} :: {lower_mask.sum():>10}")
        logger.info(f"* {'Upper hit':<30} :: {upper_mask.sum():>10}")

        # number of doublets by hand
        # lower = self.simhits[lower_mask][doublet_cols]
        # upper = self.simhits[upper_mask][doublet_cols]
        # doublets = lower.merge(upper, on=doublet_cols, how="inner")
        # logger.info(f"* {'Doublets (by hand)':<30} :: {len(doublets):>10}")

        # number of doublets
        mask = np.ones(len(self.doublets), dtype=bool)
        for [req, label] in [
            [self.doublets["simhit_system"] == OUTER_TRACKER_BARREL, "Doublets in OTB"],
            [self.doublets["simhit_layer_div_2"] == the_doublelayer, f"Doublets in layers {layers}"],
            # [self.doublets["simhit_sensor"] == 20, "z-sensor 20"],
            # [self.doublets["simhit_module"] == 0, "phi-module 0"],
            [np.abs(self.doublets["doublet_dz"]) < DZ_CUT[the_doublelayer], f"Doublets with |dz| < {DZ_CUT[the_doublelayer]}mm"],
            [np.abs(self.doublets["doublet_dr"]) < DR_CUT[the_doublelayer], f"Doublets with |dr| < {DR_CUT[the_doublelayer]}mm"],
        ]:
            mask &= req
            logger.info(f"* {label:<30} :: {mask.sum():>10}")

        # if mask.sum() < 50:
        #     # for z in sorted(list(self.doublets[mask]["simhit_z_lower"]), reverse=True):
        #     #     logger.info(f"lower z = {z}")
        #     # for dz in sorted(list(np.abs(self.doublets[mask]["doublet_dz"])), reverse=True):
        #     #     logger.info(f"dz = {dz}")


    def plot_time(self, pdf: PdfPages):
        logger.info(f"Plotting time")
        xlabel = "Sim. hit time [ns]" + r" minus $R/c$"
        for (system, simhits) in self.simhits.groupby("simhit_system"):
            bins = np.linspace(-10, 20, 301)
            fig, ax = plt.subplots()
            ax.hist(
                simhits["simhit_t_corrected"],
                bins=bins,
                histtype="stepfilled",
                color="yellow",
                edgecolor="black",
                linewidth=1.0,
                alpha=0.9,
            )
            ax.set_xlabel(xlabel)
            ax.set_ylabel("Sim. hits")
            ax.set_title(f"{NICKNAMES[system]}")
            ax.semilogy()
            ax.set_ylim(0.8, None)
            pdf.savefig()
            plt.close()


    def plot_layer_occupancy_1d(self, pdf: PdfPages):
        logger.info(f"Plotting layer occupancy (1d)")
        for (system, simhits) in self.simhits.groupby("simhit_system"):
            bins = np.arange(simhits["simhit_layer"].min()-0.5,
                             simhits["simhit_layer"].max()+1.0,
                             1)
            fig, ax = plt.subplots()
            ax.hist(
                simhits["simhit_layer"],
                bins=bins,
                histtype="stepfilled",
                color="yellow",
                edgecolor="black",
                linewidth=1.0,
                alpha=0.9,
            )
            # ax.set_ylim(0, 280e3)
            ax.set_xlabel("Layer")
            ax.set_ylabel("Sim. hits")
            ax.set_title(f"{NICKNAMES[system]}")
            pdf.savefig()
            plt.close()


    def plot_layer_occupancy_2d(self, pdf: PdfPages):
        logger.info(f"Plotting layer occupancy (2d)")
        for ((system, layer), simhits) in self.simhits.groupby(["simhit_system",
                                                                "simhit_layer",
                                                                ]):
            logger.info(f"Occupancy of {NICKNAMES[system]} layer {layer}: {len(simhits)} sim hits")
            if len(simhits) == 0:
                continue
            bins = [
                np.arange(-0.5, simhits["simhit_module"].max()+1.5, 1),
                np.arange(-0.5, simhits["simhit_sensor"].max()+1.5, 1),
            ]
            fig, ax = plt.subplots()
            _, _, _, im = ax.hist2d(
                simhits["simhit_module"],
                simhits["simhit_sensor"],
                bins=bins,
                cmap="gist_rainbow",
                norm=colors.LogNorm(vmin=0.9),
            )
            ax.set_xlabel("Phi module")
            ax.set_ylabel("Z sensor")
            ax.set_title(f"{NICKNAMES[system]}, layer {layer}")
            fig.colorbar(im, ax=ax, pad=0.01, label="Number of sim. hits")
            pdf.savefig()
            plt.close()


    def plot_radius_vs_layer(self, pdf: PdfPages):
        logger.info(f"Plotting radius vs layer")
        for (system, simhits) in self.simhits.groupby("simhit_system"):
            bins = [
                np.arange(simhits["simhit_layer"].min() - 0.5,
                          simhits["simhit_layer"].max() + 1.0, 1),
                np.arange(simhits["simhit_r"].min() - 100,
                          simhits["simhit_r"].max() + 100, 1),
                # np.linspace(0, 1600, 1600),
            ]
            fig, ax = plt.subplots()
            _, _, _, im = ax.hist2d(
                simhits["simhit_layer"],
                simhits["simhit_r"],
                bins=bins,
                cmap="gist_rainbow",
                cmin=0.5,
            )
            fig.colorbar(im, ax=ax, label="Number of sim. hits", pad=0.01)
            ax.set_xlabel("Layer")
            ax.set_ylabel("Radius")
            ax.set_title(f"{NICKNAMES[system]}")
            fig.subplots_adjust(right=0.95)
            pdf.savefig()
            plt.close()


    def doublet_requirements(self, doublets: pd.DataFrame, req: str) -> tuple[str, pd.DataFrame]:
        # return description and mask
        doublelayer = doublets["simhit_layer_div_2"]
        if len(doublelayer.unique()) != 1:
            raise ValueError(f"Multiple doublelayers found: {doublelayer.unique()}")
        doublelayer = doublelayer.iloc[0]
        if req == REQ_PASSTHROUGH:
            text = "No requirement"
            mask = np.ones(len(doublets), dtype=bool)
        elif req == REQ_XY:
            text = f"|dr| < {DR_CUT[doublelayer]}mm"
            mask = np.abs(doublets["doublet_dr"]) < DR_CUT[doublelayer]
        elif req == REQ_RZ:
            text = f"|dz| < {DZ_CUT[doublelayer]}mm"
            mask = np.abs(doublets["doublet_dz"]) < DZ_CUT[doublelayer]
        elif req == REQ_RZ_XY:
            text = f"|dr| < {DR_CUT[doublelayer]}mm, |dz| < {DZ_CUT[doublelayer]}mm"
            mask = (
                (np.abs(doublets["doublet_dz"]) < DZ_CUT[doublelayer]) &
                (np.abs(doublets["doublet_dr"]) < DR_CUT[doublelayer])
            )
        else:
            raise ValueError(f"Unknown requirement: {req}")
        return text, mask


    def plot_doublet_occupancy(self, pdf: PdfPages):
        for ((system, doublelayer), group) in self.doublets.groupby(["simhit_system",
                                                                     "simhit_layer_div_2",
                                                                    ]):
            zmax = None
            for req in DOUBLET_REQS:

                req_text, req_mask = self.doublet_requirements(group, req)
                doublets = group[req_mask]

                logger.info(f"Occupancy of {NICKNAMES[system]} doublelayer {doublelayer}, {req}: {len(doublets)} doublets")
                if len(doublets) == 0:
                    continue

                layers = [doublelayer * 2, doublelayer * 2 + 1]

                # skip these plots to save time
                # if not self.signal:
                #     continue

                # doublets = self.doublets[mask]
                bins = [
                    np.arange(-0.5, doublets["simhit_module"].max()+1.5, 1),
                    np.arange(-0.5, doublets["simhit_sensor"].max()+1.5, 1),
                ]
                fig, ax = plt.subplots()
                h2d, _, _, im = ax.hist2d(
                    doublets["simhit_module"],
                    doublets["simhit_sensor"],
                    bins=bins,
                    cmap="gist_rainbow",
                    norm=colors.LogNorm(vmin=0.9),
                )
                if zmax is None:
                    zmax = h2d.max()
                im.set_clim(0.9, zmax)
                ax.set_xlabel("Phi module")
                ax.set_ylabel("Z sensor")
                ax.set_title(f"{NICKNAMES[system]}, layers {layers}, {req_text}")
                fig.colorbar(im, ax=ax, label="Number of doublets", pad=0.01)
                pdf.savefig()
                plt.close()


    def write_denominator_info(self, pdf: PdfPages):
        logger.info(f"Writing efficiency denominator info")
        text = f"Efficiency denominator:"
        function = inspect.getsource(self.get_denominator_mask)
        function = textwrap.dedent(function)
        fig, ax = plt.subplots(figsize=(8, 8))
        args = {"ha":"left", "va":"top", "fontfamily":"monospace"}
        ax.text(0.0, 0.9, text, **args, fontsize=16)
        ax.text(0.0, 0.8, function, **args, fontsize=10)
        ax.axis("off")
        pdf.savefig()
        plt.close()


    def plot_doublet_efficiency_vs_kinematics(self, pdf: PdfPages):

        bins = {
            "mcp_pt": np.linspace(0.0, 10.0, 201),
            "mcp_eta": np.linspace(-0.7, 0.7, 281),
            "mcp_phi": np.linspace(-3.2, 3.2, 321),
        }
        xlabel = {
            "mcp_pt": r"Muon $p_T$ [GeV]",
            "mcp_eta": r"Muon $\eta$",
            "mcp_phi": r"Muon $\phi$ [rad]",
        }

        # denominator
        dmask = self.get_denominator_mask()
        denom = self.mcps[dmask][["file", "i_event", "i_mcp", "mcp_pt", "mcp_eta", "mcp_phi"]]
        if denom.duplicated().any():
            raise ValueError("Denominator has duplicated rows!")

        # numerator
        doublet_cols = [
            "file",
            "i_event", # the event
            "simhit_system", # the system (IT, OT)
            "simhit_layer_div_2", # the double layer
            "simhit_module", # the phi-module
            "simhit_sensor", # the z-sensor
        ]

        # filter doublets to only those with same parent mcp
        same_parent = self.doublets["i_mcp"] >= 0
        doublets = self.doublets[same_parent][ doublet_cols + ["i_mcp"] ].drop_duplicates()

        # check if doublets's [file, i_event, i_mcp] is in denominator
        for kin in ["mcp_pt", "mcp_eta", "mcp_phi"]:
            for ((system, doublelayer), group) in doublets.groupby(["simhit_system",
                                                                    "simhit_layer_div_2",
                                                                    ]):
                layers = [doublelayer * 2, doublelayer * 2 + 1]

                doublet_keys = group[["file", "i_event", "i_mcp"]].drop_duplicates()
                merged = denom.merge(doublet_keys, on=["file", "i_event", "i_mcp"], how="inner")

                n_denom, edges = np.histogram(denom[kin], bins=bins[kin])
                n_numer, edges = np.histogram(merged[kin], bins=bins[kin])
                efficiency = np.divide(n_numer, n_denom, out=np.zeros_like(n_numer, dtype=float), where=n_denom!=0)
                centers = 0.5 * (edges[1:] + edges[:-1])
                fig, ax = plt.subplots()
                ax.plot(
                    centers,
                    efficiency,
                    marker="o",
                    markersize=1,
                    linestyle="-",
                    color="dodgerblue",
                )
                ax.set_xlabel(xlabel[kin])
                ax.set_ylabel("Doublet finding efficiency")
                ax.set_title(f"{NICKNAMES[system]}, layers {layers}")
                ax.set_ylim(0.7, 1.03)
                pdf.savefig()
                plt.close()


    def get_denominator_mask(self):
        mask = (
            (self.mcps["mcp_pdg"].isin([MUON, ANTIMUON])) &
            (self.mcps["mcp_q"] != 0) &
            (self.mcps["mcp_pt"] > ONE_POINT_FIVE_GEV) &
            (self.mcps["mcp_vertex_r"] < ZERO_POINT_ZERO_ONE_MM) &
            (np.abs(self.mcps["mcp_vertex_z"]) < ZERO_POINT_ZERO_ONE_MM) &
            (np.abs(self.mcps["mcp_eta"]) < BARREL_TRACKER_MAX_ETA)
        )
        return mask


    def add_simhit_mcp_features(self):
        mcp_cols = [
            "mcp_p",
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
            "mcp_pdg",
            "mcp_q",
            "mcp_vertex_r",
            "mcp_vertex_z",
        ]
        if not self.signal:
            raise ValueError("Should not be calling add_simhit_mcp_features for background")
        self.simhits = self.simhits.merge(
            self.mcps[["file", "i_event", "i_mcp", *mcp_cols]],
            on=["file", "i_event", "i_mcp"],
            how="left",
            validate="many_to_one",
        )
        self.simhits[mcp_cols] = self.simhits[mcp_cols].fillna(0)


    def add_doublet_mcp_features(self):
        logger.info("Adding doublet mcp features ...")
        if not self.signal:
            raise ValueError("Should not be calling add_doublet_mcp_features for background")
        # add mcp features when the doublet i_mcp lower and upper match
        # otherwise, assign 0
        mcp_cols = [
            "mcp_p",
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
            "mcp_pdg",
            "mcp_q",
            "mcp_vertex_r",
            "mcp_vertex_z",
            "mcp_qoverpt",
        ]
        merged = self.doublets.merge(
            self.mcps[["file", "i_event", "i_mcp", *mcp_cols]],
            left_on=["file", "i_event", "i_mcp"],
            right_on=["file", "i_event", "i_mcp"],
            how="left",
            validate="many_to_one",
        ) # .drop(columns=["i_mcp"])
        mask = merged["i_mcp"] >= 0 # merged["i_mcp_lower"].eq(merged["i_mcp_upper"])
        self.doublets[mcp_cols] = merged[mcp_cols].where(mask, 0).fillna(0)


    def add_linesegment_mcp_features(self):
        logger.info("Adding line segment mcp features ...")
        if not self.signal:
            raise ValueError("Should not be calling add_linesegment_mcp_features for background")
        # add mcp features when the line segment i_mcp lower and upper match
        # otherwise, assign 0
        mcp_cols = [
            "mcp_p",
            "mcp_pt",
            "mcp_eta",
            "mcp_phi",
            "mcp_pdg",
            "mcp_q",
            "mcp_vertex_r",
            "mcp_vertex_z",
            "mcp_qoverpt",
        ]
        merged = self.linesegments.merge(
            self.mcps[["file", "i_event", "i_mcp", *mcp_cols]],
            left_on=["file", "i_event", "i_mcp"],
            right_on=["file", "i_event", "i_mcp"],
            how="left",
            validate="many_to_one",
        )
        mask = merged["i_mcp"] >= 0
        self.linesegments[mcp_cols] = merged[mcp_cols].where(mask, 0).fillna(0)


    def plot_doublet_features(self, pdf: PdfPages):
        logger.info("Plotting doublet features ...")
        baseline = self.baseline_doublet_mask() if self.signal else np.ones(len(self.doublets), dtype=bool)

        bins = {
            "doublet_dz": np.linspace(-150, 150, 301) if self.signal else np.linspace(-49e3, 49e3, 101),
            "doublet_dr": np.linspace(0, 1000, 101) if self.signal else np.linspace(0, 1500, 101),
            "doublet_dphi": np.linspace(-1.0, 1.0, 201) if self.signal else np.linspace(-3.2, 3.2, 201),
            "doublet_pt": np.linspace(0, 10, 101),
            "doublet_qoverpt": np.linspace(-0.8, 0.8, 161),
            "mcp_qoverpt": np.linspace(-0.8, 0.8, 161),
            "mc_pt": np.linspace(0, 10, 101),
        }
        xlabel = {
            "doublet_dz": r"dz in rz-plane [mm]",
            "doublet_dr": r"dr in xy-plane [mm]",
            "doublet_dphi": r"dphi in xy-plane [rad]",
            "doublet_pt": r"pT [GeV]",
            "doublet_qoverpt": r"Doublet q/pT [1/GeV]",
            "mcp_qoverpt": r"MC q/pT [1/GeV]",
            "mc_pt": r"MC pT [GeV]",

        }
        formatting = {
            "doublet_dz": ".1f",
            "doublet_dr": ".0f",
            "doublet_dphi": ".3f",
            "doublet_pt": ".1f",
            "doublet_qoverpt": ".3f",
            "mcp_qoverpt": ".3f",
        }

        # 1d histograms
        for feature in [
            "doublet_dz",
            "doublet_dr",
            "doublet_dphi",
            "doublet_pt",
        ]:

            for semilogy in [
                False,
                True,
            ]:

                for ((system, doublelayer), group) in self.doublets[baseline].groupby(["simhit_system",
                                                                                       "simhit_layer_div_2",
                                                                                       ]):

                        logger.info(f"Plotting signal doublet feature {feature}, system {system}, doublelayer {doublelayer} ...")
                        layers = [doublelayer * 2, doublelayer * 2 + 1]
                        if len(group) == 0:
                            continue

                        fig, ax = plt.subplots()
                        ax.hist(
                            group[feature],
                            bins=bins[feature],
                            histtype="stepfilled",
                            color="crimson",
                            edgecolor="black",
                            linewidth=1.0,
                            alpha=0.9,
                        )
                        if semilogy:
                            ax.semilogy()
                        num = len(group)
                        mean = np.mean(group[feature])
                        rms = np.sqrt(np.mean((group[feature] - mean) ** 2))
                        p997 = np.percentile(np.abs(group[feature]), 99.7)
                        fmt = formatting[feature]
                        ax.set_ylim(0.8 if semilogy else 0, None)
                        ax.set_xlabel(xlabel[feature])
                        ax.set_ylabel("Doublets")
                        ax.set_title(f"{NICKNAMES[system]} layers {layers}. N={num}, Mean={mean:{fmt}}, RMS={rms:{fmt}}")
                        ax.text(0.05, 0.95, f"99.7% in {p997:{fmt}}", transform=ax.transAxes)
                        pdf.savefig()
                        plt.close()


        # 2d histograms
        for feature_x, feature_y in [
            ("doublet_dphi", "doublet_dr"),
            ("doublet_dphi", "mcp_qoverpt"),
            ("doublet_qoverpt", "mcp_qoverpt"),
        ]:

            if not self.signal and any(["mcp" in feat for feat in [feature_x, feature_y]]):
                continue

            for ((system, doublelayer), group) in self.doublets[baseline].groupby(["simhit_system",
                                                                                    "simhit_layer_div_2",
                                                                                    ]):

                logger.info(f"Plotting signal doublet features {feature_x} vs {feature_y}, system {system}, doublelayer {doublelayer} ...")
                layers = [doublelayer * 2, doublelayer * 2 + 1]
                if len(group) == 0:
                    continue

                fig, ax = plt.subplots()
                h2d, _, _, im = ax.hist2d(
                    group[feature_x],
                    group[feature_y],
                    bins=[bins[feature_x], bins[feature_y]],
                    cmap="gist_rainbow",
                    cmin=0.5,
                )
                if np.nansum(h2d) == 0:
                    raise ValueError(f"No entries in 2d histogram. Fix the binning!")
                fig.colorbar(im, ax=ax, label="Doublets", pad=0.01)
                num = len(group)
                ax.set_xlabel(xlabel[feature_x])
                ax.set_ylabel(xlabel[feature_y])
                ax.set_title(f"{NICKNAMES[system]} layers {layers}. N={num}")
                pdf.savefig()
                plt.close()



    def baseline_doublet_mask(self) -> pd.Series:
        return (
            first_exit_mask(self.doublets) &
            (self.doublets["i_mcp_lower"] == self.doublets["i_mcp_upper"]) &
            (self.doublets["mcp_pdg"].isin([MUON, ANTIMUON])) &
            (self.doublets["mcp_q"] != 0) &
            (self.doublets["mcp_pt"] > ONE_POINT_FIVE_GEV) &
            (np.abs(self.doublets["mcp_eta"]) < BARREL_TRACKER_MAX_ETA) &
            (self.doublets["mcp_vertex_r"] < ZERO_POINT_ZERO_ONE_MM) &
            (np.abs(self.doublets["mcp_vertex_z"]) < ZERO_POINT_ZERO_ONE_MM) &
            np.ones(len(self.doublets), dtype=bool)
        )


    def plot_doublet_quality_efficiency(self, pdf: PdfPages):

        bins = {
            "mcp_pt": np.linspace(0.0, 10.0, 201),
            "mcp_eta": np.linspace(-0.7, 0.7, 281),
            "mcp_phi": np.linspace(-3.2, 3.2, 321),
        }
        xlabel = {
            "mcp_pt": r"Muon $p_T$ [GeV]",
            "mcp_eta": r"Muon $\eta$",
            "mcp_phi": r"Muon $\phi$ [rad]",
        }

        # only consider truth-match doublets
        baseline = self.baseline_doublet_mask()
        logger.info(f"Doublet efficiency: total doublets: {len(self.doublets)}")
        logger.info(f"Doublet efficiency: total doublets in baseline: {baseline.sum()}")

        # todo: add comment
        for i_kin, kin in enumerate([
            "mcp_pt",
            "mcp_eta",
            "mcp_phi"
        ]):

            for ((system, doublelayer), group) in self.doublets[baseline].groupby(["simhit_system",
                                                                                   "simhit_layer_div_2",
                                                                                   ]):

                logger.info(f"Plotting doublet quality efficiency vs {kin}, system {system}, doublelayer {doublelayer} ...")
                layers = [doublelayer * 2, doublelayer * 2 + 1]

                for req in DOUBLET_REQS:
                    req_text, req_mask = self.doublet_requirements(group, req)
                    denom = group
                    numer = group[req_mask]
                    if i_kin == 0:
                        logger.info(f"Denom for system {system} layers {layers} {req}: {len(denom)} doublets")
                        logger.info(f"Numer for system {system} layers {layers} {req}: {len(numer)} doublets")

                    n_denom, edges = np.histogram(denom[kin], bins=bins[kin])
                    n_numer, edges = np.histogram(numer[kin], bins=bins[kin])
                    efficiency = np.divide(n_numer, n_denom, out=np.zeros_like(n_numer, dtype=float), where=n_denom!=0)
                    centers = 0.5 * (edges[1:] + edges[:-1])

                    fig, ax = plt.subplots()
                    ax.plot(
                        centers,
                        efficiency,
                        marker="o",
                        markersize=1,
                        linestyle="-",
                        color="dodgerblue",
                    )
                    ax.set_xlabel(xlabel[kin])
                    ax.set_ylabel("Doublet quality efficiency")
                    ax.set_title(f"{NICKNAMES[system]} layers {layers}: {req_text}")
                    ax.set_ylim(0.965, 1.004)
                    pdf.savefig()
                    plt.close()


    def write_doublet_denominator_info(self, pdf: PdfPages):
        text = f"Double quality efficiency denominator:"
        function = inspect.getsource(first_exit_mask)
        function = textwrap.dedent(function)
        fig, ax = plt.subplots(figsize=(8, 8))
        args = {"ha":"left", "va":"top", "fontfamily":"monospace"}
        ax.text(-0.1, 0.9, text, **args, fontsize=16)
        ax.text(-0.1, 0.8, function, **args, fontsize=10)
        ax.text(-0.1, 0.4, f"MIN_COSTHETA = {MIN_COSTHETA}")
        ax.text(-0.1, 0.3, f"MAX_TIME = {MAX_TIME} ns")
        ax.text(-0.1, 0.2, f"MIN_SIMHIT_PT_FRACTION = {MIN_SIMHIT_PT_FRACTION}")
        ax.axis("off")
        pdf.savefig()
        plt.close()


    def baseline_linesegment_mask(self) -> pd.Series:
        dl_lower = self.linesegments["doublet_doublelayer_lower"]
        dl_upper = self.linesegments["doublet_doublelayer_upper"]
        return (
            first_exit_mask_ls(self.linesegments) &
            (self.linesegments["i_mcp"] >= 0) &
            (self.linesegments["mcp_pdg"].isin([MUON, ANTIMUON])) &
            (self.linesegments["mcp_q"] != 0) &
            (self.linesegments["mcp_pt"] > ONE_POINT_FIVE_GEV) &
            (np.abs(self.linesegments["mcp_eta"]) < BARREL_TRACKER_MAX_ETA) &
            (self.linesegments["mcp_vertex_r"] < ZERO_POINT_ZERO_ONE_MM) &
            (np.abs(self.linesegments["mcp_vertex_z"]) < ZERO_POINT_ZERO_ONE_MM) &
            (np.abs(self.linesegments["doublet_dr_lower"]) < DR_CUT[dl_lower]) &
            (np.abs(self.linesegments["doublet_dr_upper"]) < DR_CUT[dl_upper]) &
            (np.abs(self.linesegments["doublet_dz_lower"]) < DZ_CUT[dl_lower]) &
            (np.abs(self.linesegments["doublet_dz_upper"]) < DZ_CUT[dl_upper]) &
            np.ones(len(self.linesegments), dtype=bool)
        )


    def plot_linesegment_features(self, pdf: PdfPages):
        logger.info("Plotting signal linesegment features ...")
        baseline = self.baseline_linesegment_mask() if self.signal else np.ones(len(self.linesegments), dtype=bool)

        bins = {
            "ls_deta": np.linspace(-3.2, 3.2, 641) if not self.signal else np.linspace(-0.011, 0.011, 221),
            "ls_dphi": np.linspace(-3.2, 3.2, 321) if not self.signal else np.linspace(-0.08, 0.08, 201),
            "ls_dr": np.linspace(0, 1500, 501) if not self.signal else np.linspace(0, 1000, 401),
            "ls_dz": np.linspace(-30000, 30000, 201) if not self.signal else np.linspace(-200, 200, 201),
            "ls_ddr": np.linspace(-300, 300, 601),
            "ls_ddz": np.linspace(-60, 60, 601),
            "ls_dqoverpt": np.linspace(-0.2, 0.2, 201),
            "ls_dtheta_rz": np.linspace(-0.024, 0.024, 241),
            "ls_dtheta_xy": np.linspace(-0.12, 0.12, 241),
        }
        xlabel = {
            "ls_deta": r"upper doublet eta - lower doublet eta",
            "ls_dphi": r"upper doublet phi - lower doublet phi [rad]",
            "ls_dr": "line segment dr [mm]",
            "ls_dz": "line segment dz [mm]",
            "ls_ddr": "upper doublet dr - lower doublet dr",
            "ls_ddz": "upper doublet dz - lower doublet dz",
            "ls_dqoverpt": "upper doublet q/pt - lower doublet q/pt",
            "ls_dtheta_rz": "upper doublet theta_rz - lower doublet theta_rz",
            "ls_dtheta_xy": "upper doublet theta_xy - lower doublet theta_xy",
        }
        formatting = {
            "ls_deta": ".5f",
            "ls_dphi": ".5f",
            "ls_dr": ".1f",
            "ls_dz": ".1f",
            "ls_ddr": ".3f",
            "ls_ddz": ".3f",
            "ls_dqoverpt": ".3f",
            "ls_dtheta_rz": ".5f",
            "ls_dtheta_xy": ".4f",
        }
        color = "cornflowerblue" if self.signal else "crimson"

        # 1d histograms
        for feature in [
            "ls_deta",
            "ls_dphi",
            "ls_dr",
            "ls_dz",
            "ls_ddr",
            "ls_ddz",
            "ls_dqoverpt",
            "ls_dtheta_rz",
            "ls_dtheta_xy",
        ]:

            for semilogy in [
                False,
                # True,
            ]:

                for ((system, doublelayer), group) in self.linesegments[baseline].groupby(["ls_system",
                                                                                           "ls_doublelayer",
                                                                                           ]):

                        logger.info(f"Plotting signal linesegment feature {feature}, system {system}, doublelayer {doublelayer} ...")

                        fig, ax = plt.subplots()
                        ax.hist(
                            group[feature],
                            bins=bins[feature],
                            histtype="stepfilled",
                            color=color,
                            edgecolor="black",
                            linewidth=1.0,
                            alpha=0.9,
                        )
                        if semilogy:
                            ax.semilogy()
                        num = len(group)
                        mean = np.mean(group[feature])
                        rms = np.sqrt(np.mean((group[feature] - mean) ** 2))
                        p997 = np.percentile(np.abs(group[feature]), 99.7)
                        fmt = formatting[feature]
                        ax.set_ylim(0.8 if semilogy else 0, None)
                        ax.set_xlabel(xlabel[feature])
                        ax.set_ylabel("Line Segments")
                        ax.set_title(f"{NICKNAMES[system]}. DL={doublelayer}. N={num}, Mean={mean:{fmt}}, RMS={rms:{fmt}}")
                        ax.text(0.05, 0.95, f"99.7% in {p997:{fmt}}", transform=ax.transAxes)
                        pdf.savefig()
                        plt.close()

        # 2d histograms
        for feature_x, feature_y in [
            ("ls_dphi", "ls_dr"),
        ]:

            for ((system, doublelayer), group) in self.linesegments[baseline].groupby(["ls_system",
                                                                                       "ls_doublelayer",
                                                                                       ]):

                logger.info(f"Plotting signal linesegment features {feature_x} vs {feature_y}, system {system}, doublelayer {doublelayer} ...")
                if len(group) == 0:
                    logger.info(f"No linesegments in {NICKNAMES[system]} doublelayer {doublelayer} passing baseline, skipping feature plot")
                    continue

                fig, ax = plt.subplots()
                _, _, _, im = ax.hist2d(
                    group[feature_x],
                    group[feature_y],
                    bins=[bins[feature_x], bins[feature_y]],
                    cmap="gist_rainbow",
                    cmin=0.5,
                )
                fig.colorbar(im, ax=ax, label="Line Segments", pad=0.01)
                num = len(group)
                ax.set_xlabel(xlabel[feature_x])
                ax.set_ylabel(xlabel[feature_y])
                ax.set_title(f"{NICKNAMES[system]} DL={doublelayer}. N={num}")
                pdf.savefig()
                plt.close()


def first_exit_mask(doublets: pd.DataFrame) -> pd.Series:
    return (
        (doublets["simhit_t_corrected_lower"] < MAX_TIME) &
        (doublets["simhit_t_corrected_upper"] < MAX_TIME) &
        (doublets["simhit_costheta_lower"] > MIN_COSTHETA) &
        (doublets["simhit_costheta_upper"] > MIN_COSTHETA) &
        (doublets["simhit_p_lower"] / doublets["mcp_p"] > MIN_SIMHIT_PT_FRACTION) &
        (doublets["simhit_p_upper"] / doublets["mcp_p"] > MIN_SIMHIT_PT_FRACTION)
    )


def first_exit_mask_ls(df: pd.DataFrame) -> pd.Series:
    return (
        (df["simhit_t_corrected_lower_lower"] < MAX_TIME) &
        (df["simhit_t_corrected_lower_upper"] < MAX_TIME) &
        (df["simhit_t_corrected_upper_lower"] < MAX_TIME) &
        (df["simhit_t_corrected_upper_upper"] < MAX_TIME) &

        (df["simhit_costheta_lower_lower"] > MIN_COSTHETA) &
        (df["simhit_costheta_lower_upper"] > MIN_COSTHETA) &
        (df["simhit_costheta_upper_lower"] > MIN_COSTHETA) &
        (df["simhit_costheta_upper_upper"] > MIN_COSTHETA) &

        (df["simhit_p_lower_lower"] / df["mcp_p"] > MIN_SIMHIT_PT_FRACTION) &
        (df["simhit_p_lower_upper"] / df["mcp_p"] > MIN_SIMHIT_PT_FRACTION) &
        (df["simhit_p_upper_lower"] / df["mcp_p"] > MIN_SIMHIT_PT_FRACTION) &
        (df["simhit_p_upper_upper"] / df["mcp_p"] > MIN_SIMHIT_PT_FRACTION)
    )

