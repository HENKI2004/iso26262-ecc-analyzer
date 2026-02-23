"""Component for trimming and distributing residual and latent fault rates after SEC-DED processing (LPDDR4)."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, SplitBlock, SumBlock
from ...interfaces import FaultType


class SecDedTrim(Base):
    """Component for trimming and distributing residual and latent fault rates after SEC-DED processing.

    This module chains sequential split operations for SBE, DBE, and TBE fault types to
    model the final trimming behavior of the LPDDR4 architecture.
    """

    def __init__(self, name: str):
        """Initializes the SecDedTrim component with predefined split parameters.

        Args:
            name (str): The descriptive name of the component.
        """
        self.spfm_sbe_split = {FaultType.SBE: 0.89}
        self.spfm_dbe_split = {FaultType.SBE: 0.20, FaultType.DBE: 0.79}
        self.spfm_tbe_split = {
            FaultType.SBE: 0.03,
            FaultType.DBE: 0.27,
            FaultType.TBE: 0.70,
        }

        self.lfm_sbe_split = {FaultType.SBE: 0.89}
        self.lfm_dbe_split = {FaultType.SBE: 0.20, FaultType.DBE: 0.79}
        self.lfm_tbe_split = {
            FaultType.SBE: 0.03,
            FaultType.DBE: 0.27,
            FaultType.TBE: 0.70,
        }

        super().__init__(name)

    def configure_blocks(self):
        """Configures the root block as a collection of split operations.

        Redistributes faults for both residual (SPFM) and latent (LFM) paths.
        """
        self.root_block = SumBlock(
            self.name,
            [
                SplitBlock("sec_trim_SPFM_SBE_Split", FaultType.SBE, self.spfm_sbe_split, is_spfm=True),
                SplitBlock("sec_trim_SPFM_DBE_Split", FaultType.DBE, self.spfm_dbe_split, is_spfm=True),
                SplitBlock("sec_trim_SPFM_TBE_Split", FaultType.TBE, self.spfm_tbe_split, is_spfm=True),
                SplitBlock("sec_trim_LFM_SBE_Split", FaultType.SBE, self.lfm_sbe_split, is_spfm=False),
                SplitBlock("sec_trim_LFM_DBE_Split", FaultType.DBE, self.lfm_dbe_split, is_spfm=False),
                SplitBlock("sec_trim_LFM_TBE_Split", FaultType.TBE, self.lfm_tbe_split, is_spfm=False),
            ],
        )
