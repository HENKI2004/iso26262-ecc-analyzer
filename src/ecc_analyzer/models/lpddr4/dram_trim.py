"""Component for trimming and distributing failure rates for the DRAM hardware layer (LPDDR4)."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, SplitBlock, SumBlock
from ...interfaces import FaultType


class DramTrim(Base):
    """Handles the redistribution of SBE, DBE, and TBE faults for both residual and latent paths.

    This component uses a SumBlock to apply parallel split operations that redistribute
    fault rates according to specific hardware trimming factors defined for LPDDR4.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the DramTrim component with hardware-specific split distribution parameters.

        Args:
            name (str): The descriptive name of the component.
        """
        self.spfm_sbe_split = {FaultType.SBE: 0.94}
        self.spfm_dbe_split = {FaultType.SBE: 0.11, FaultType.DBE: 0.89}
        self.spfm_tbe_split = {
            FaultType.SBE: 0.009,
            FaultType.DBE: 0.15,
            FaultType.TBE: 0.83,
        }

        self.lfm_sbe_split = {FaultType.SBE: 0.94}
        self.lfm_dbe_split = {FaultType.SBE: 0.11, FaultType.DBE: 0.89}

        super().__init__(name, total_fit)

    def configure_blocks(self):
        """Configures the root block as a collection of split operations.

        Each split block redistributes the specified fault type according to the defined ratios.
        Both SPFM (residual) and LFM (latent) paths are processed in parallel.
        """
        self.root_block = SumBlock(
            self.name,
            [
                SplitBlock("dram_SPFM_SBE_Split", FaultType.SBE, self.spfm_sbe_split, is_spfm=True),
                SplitBlock("dram_SPFM_DBE_Split", FaultType.DBE, self.spfm_dbe_split, is_spfm=True),
                SplitBlock("dram_SPFM_TBE_Split", FaultType.TBE, self.spfm_tbe_split, is_spfm=True),
                SplitBlock("dram_LFM_SBE_Split", FaultType.SBE, self.lfm_sbe_split, is_spfm=False),
                SplitBlock("dram_LFM_DBE_Split", FaultType.DBE, self.lfm_dbe_split, is_spfm=False),
            ],
        )
