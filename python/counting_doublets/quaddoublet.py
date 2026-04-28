"""
This module defines the QuadDoublet class, which creates a quad doublet from two line segments.
All line segments in layers 0-3 are considered for combination with line segments in layer 4-7.
The line segments are combined if they satisfy goodness criteria.
To avoid filling the memory with all possible combinations, combination is done with a groupby approach.

"""

import numpy as np
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from constants import BYTE_TO_MB, NO_MCP

class QuadDoublet:

    def __init__(self, linesegments: pd.DataFrame, signal: bool, cut_quad_doublets: bool):
        self.df = None
        self.signal = signal
        self.cut_quad_doublets = cut_quad_doublets
        self.linesegments = linesegments.copy()
        memory = self.linesegments.memory_usage(deep=True).sum() * BYTE_TO_MB
        logger.info(f"Making quad doublets. Line segments dataframe size: {memory:.2f} MB")
        self.prep_linesegments()
        self.make_quad_doublets()


    def prep_linesegments(self) -> None:
        logger.info("Preprocessing line segments for quad doublet making ...")


    def make_quad_doublets(self) -> None:
        logger.info("Making quad doublets ...")

        # one loop for now:
        # layers 0123 combined with layers 4567
        # equivalently, doublelayers 01 combined with 23 (doublelayer // 4 == 0)

        groupby_cols = [
            "file",
            "ls_system",
            "ls_doublelayer_div_4",
            "ls_doublelayer_even",
        ]
        n_group = len(self.linesegments.groupby(groupby_cols))

        for i_group, (cols, df) in enumerate(self.linesegments.groupby(groupby_cols)):
            logger.info(f"Processing group {i_group} / {n_group} for quaddoublets (n={len(df)}) ...")
            logger.info(cols)


