"""Component for trimming and distributing failure rates across the bus architecture (LPDDR5)."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, SplitBlock, SumBlock
from ...interfaces import FaultType


class BusTrim(Base):
    """Component for trimming and distributing failure rates across the bus architecture.

    This module injects specific bus-related fault sources (AZ) and redistributes
    SBE, DBE, and TBE faults for both SPFM and LFM paths based on LPDDR5 specifications.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the BusTrim component with bus-specific split parameters.

        Args:
            name (str): The descriptive name of the component.
        """
        self.spfm_sbe_split = {FaultType.SBE: 0.438}
        self.spfm_dbe_split = {FaultType.SBE: 0.496, FaultType.DBE: 0.314}
        self.spfm_tbe_split = {
            FaultType.SBE: 0.325,
            FaultType.DBE: 0.419,
            FaultType.TBE: 0.175,
        }

        dram_fit = total_fit
        self.spfm_az_source = 0.0748 * dram_fit
        self.spfm_lb_source = 0.1

        self.lfm_sbe_split = self.spfm_sbe_split
        self.lfm_dbe_split = self.spfm_dbe_split
        self.lfm_tbe_split = self.spfm_tbe_split
        super().__init__(name, total_fit)

    def configure_blocks(self):
        """Configures the root block as a collection of fault injections and split operations.

        Uses a SumBlock to aggregate the source injection (AZ) and the parallel
        redistribution (SplitBlocks) of incoming faults.
        """
        self.root_block = SumBlock(
            self.name,
            [
                BasicEvent("Bus", FaultType.AZ, self.spfm_az_source, is_spfm=True),
                BasicEvent("Bus", FaultType.LB, self.spfm_lb_source, is_spfm=True),
                SplitBlock("BUS_SPFM_SBE_Split", FaultType.SBE, self.spfm_sbe_split, is_spfm=True),
                SplitBlock("BUS_SPFM_DBE_Split", FaultType.DBE, self.spfm_dbe_split, is_spfm=True),
                SplitBlock("BUS_SPFM_TBE_Split", FaultType.TBE, self.spfm_tbe_split, is_spfm=True),
            ],
        )
