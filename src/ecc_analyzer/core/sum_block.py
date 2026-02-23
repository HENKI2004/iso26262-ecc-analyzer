"""Parallel block that aggregates FIT rates from multiple sub-blocks."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ..interfaces import BlockInterface, FaultType


class SumBlock(BlockInterface):
    """Parallel block that aggregates FIT rates from multiple sub-blocks.

    Manages path junctions by executing sub-blocks in parallel (starting from the
    same input state) and calculating the sum of their individual contributions
    (deltas) to the total system rates.
    """

    def __init__(self, name: str, sub_blocks: list[BlockInterface]):
        """Initializes the SumBlock with a list of parallel sub-blocks.

        Args:
            name (str): The descriptive name of the aggregation block.
            sub_blocks (list[BlockInterface]): List of blocks whose results will be summed.
        """
        self.name = name
        self.sub_blocks = sub_blocks

    def compute_fit(self, spfm_rates: dict[FaultType, float], lfm_rates: dict[FaultType, float]) -> tuple[dict[FaultType, float], dict[FaultType, float]]:
        """Aggregates the FIT rate transformations from all internal parallel blocks.

        Calculates the delta contribution of each block relative to the input state
        and sums these deltas to produce the final output state.

        Args:
            spfm_rates (dict[FaultType, float]): Current residual failure rates (Input state).
            lfm_rates (dict[FaultType, float]): Current latent failure rates (Input state).

        Returns:
            tuple[dict[FaultType, float], dict[FaultType, float]]: A tuple containing:
                - Final aggregated SPFM rates.
                - Final aggregated LFM rates.
        """
        total_spfm = spfm_rates.copy()
        total_lfm = lfm_rates.copy()
        for block in self.sub_blocks:
            res_spfm, res_lfm = block.compute_fit(spfm_rates, lfm_rates)
            for fault in set(res_spfm.keys()) | set(spfm_rates.keys()):
                delta = res_spfm.get(fault, 0.0) - spfm_rates.get(fault, 0.0)
                if delta != 0:
                    total_spfm[fault] = total_spfm.get(fault, 0.0) + delta
            for fault in set(res_lfm.keys()) | set(lfm_rates.keys()):
                delta = res_lfm.get(fault, 0.0) - lfm_rates.get(fault, 0.0)
                if delta != 0:
                    total_lfm[fault] = total_lfm.get(fault, 0.0) + delta
        return total_spfm, total_lfm

    def to_dict(self):
        """Serializes the SumBlock into a dictionary for configuration export.

        Returns:
            dict: A dictionary containing the block type and all parameters
                needed to reconstruct this SumBlock via the BlockFactory.
        """

        return {"type": "SumBlock", "name": self.name, "sub_blocks": [block.to_dict() for block in self.sub_blocks]}

    def compute_symbolic_fit(self, spfm_exprs, lfm_exprs, mode):
        total_spfm = spfm_exprs.copy()
        total_lfm = lfm_exprs.copy()

        for block in self.sub_blocks:
            res_spfm, res_lfm = block.compute_symbolic_fit(spfm_exprs, lfm_exprs, mode)

            # Aggregiere die SPFM Deltas
            for fault in set(res_spfm.keys()) | set(spfm_exprs.keys()):
                delta = res_spfm.get(fault, 0) - spfm_exprs.get(fault, 0)
                total_spfm[fault] = total_spfm.get(fault, 0) + delta

            # Aggregiere die LFM Deltas
            for fault in set(res_lfm.keys()) | set(lfm_exprs.keys()):
                delta = res_lfm.get(fault, 0) - lfm_exprs.get(fault, 0)
                total_lfm[fault] = total_lfm.get(fault, 0) + delta

        return total_spfm, total_lfm
