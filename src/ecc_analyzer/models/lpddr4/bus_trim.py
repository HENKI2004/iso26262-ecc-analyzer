"""Component for trimming and distributing failure rates across the bus architecture (LPDDR4)."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, SplitBlock, SumBlock
from ...interfaces import FaultType


class BusTrim(Base):
    """Component for trimming and distributing failure rates across the bus architecture.

    This module injects specific bus-related fault sources (MBE, AZ) and redistributes
    SBE, DBE, and TBE faults for both SPFM and LFM paths.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the BusTrim component with LPDDR4-specific split parameters.

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

        self.lfm_sbe_split = {FaultType.SBE: 0.438}
        self.lfm_dbe_split = {FaultType.SBE: 0.496, FaultType.DBE: 0.314}
        dram_fit = total_fit
        self.spfm_mbe_source = 0.001 * dram_fit
        self.spfm_az_source = 0.0748 * dram_fit

        super().__init__(name, total_fit)

    def configure_blocks(self):
        """Configures the root block as a collection of fault injections and split operations.

        Uses a SumBlock to aggregate source injections and parallel redistribution
        (SplitBlocks) of incoming faults.
        """
        self.root_block = SumBlock(
            self.name,
            [
                BasicEvent("bus", FaultType.MBE, self.spfm_mbe_source, is_spfm=True),
                BasicEvent("bus", FaultType.AZ, self.spfm_az_source, is_spfm=True),
                SplitBlock("bus_SPFM_SBE_Split", FaultType.SBE, self.spfm_sbe_split, is_spfm=True),
                SplitBlock("bus_SPFM_DBE_Split", FaultType.DBE, self.spfm_dbe_split, is_spfm=True),
                SplitBlock("bus_SPFM_TBE_Split", FaultType.TBE, self.spfm_tbe_split, is_spfm=True),
                SplitBlock("bus_LFM_SBE_Split", FaultType.SBE, self.lfm_sbe_split, is_spfm=False),
                SplitBlock("bus_LFM_DBE_Split", FaultType.DBE, self.lfm_dbe_split, is_spfm=False),
            ],
        )
