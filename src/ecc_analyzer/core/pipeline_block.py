"""Executes a sequence of logic blocks for FIT rate transformations."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ..interfaces import BlockInterface, FaultType


class PipelineBlock(BlockInterface):
    """Executes a sequence of blocks where the output of one block becomes the input of the next.

    This block type is used to model serial hardware paths or sequential processing steps
    (e.g., Source -> ECC -> Trim).
    """

    def __init__(self, name: str, sub_blocks: list[BlockInterface]):
        """Initializes the PipelineBlock with a sequence of sub-blocks.

        Args:
            name (str): The descriptive name of the pipeline.
            sub_blocks (list[BlockInterface]): A list of blocks implementing BlockInterface
                to be executed in strict sequential order.
        """
        self.name = name
        self.sub_blocks = sub_blocks

    def compute_fit(self, spfm_rates: dict[FaultType, float], lfm_rates: dict[FaultType, float]) -> tuple[dict[FaultType, float], dict[FaultType, float]]:
        """Sequentially processes all blocks in the pipeline.

        Passes the output rates of one block as the input to the next block in the list.

        Args:
            spfm_rates (dict[FaultType, float]): Initial residual failure rates entering the pipeline.
            lfm_rates (dict[FaultType, float]): Initial latent failure rates entering the pipeline.

        Returns:
            tuple[dict[FaultType, float], dict[FaultType, float]]: A tuple containing:
                - Final SPFM rates after the last block.
                - Final LFM rates after the last block.
        """
        current_spfm = spfm_rates.copy()
        current_lfm = lfm_rates.copy()

        for block in self.sub_blocks:
            current_spfm, current_lfm = block.compute_fit(current_spfm, current_lfm)

        return current_spfm, current_lfm

    def to_dict(self):
        """Serializes the PipelineBlock into a dictionary for configuration export.

        Returns:
            dict: A dictionary containing the block type and all parameters
                needed to reconstruct this PipelineBlock via the BlockFactory.
        """

        return {"type": "PipelineBlock", "name": self.name, "sub_blocks": [block.to_dict() for block in self.sub_blocks]}

    def compute_symbolic_fit(self, spfm_exprs, lfm_exprs, mode):
        current_spfm = spfm_exprs.copy()
        current_lfm = lfm_exprs.copy()

        for block in self.sub_blocks:
            current_spfm, current_lfm = block.compute_symbolic_fit(current_spfm, current_lfm, mode)

        return current_spfm, current_lfm
