"""Component for Single Error Correction (SEC) in LPDDR5 architectures."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, CoverageBlock, SplitBlock, SumBlock
from ...interfaces import FaultType


class Sec(Base):
    """Component for Single Error Correction (SEC) in LPDDR5.

    This module handles SBE coverage (correcting single bit errors) and redistributes
    DBE failure rates (Double Bit Errors splitting into TBE). It also introduces
    a latent Single Bit (SB) fault source.
    """

    def __init__(self, name: str):
        """Initializes the SEC component.

        Args:
            name (str): The descriptive name of the component.
        """
        self.sbe_dc_residual = 1.0
        self.sbe_dc_latent = 0.0

        self.dbe_to_dbe_p = 0.83
        self.dbe_to_tbe_p = 0.17

        self.sb_source = 0.1

        super().__init__(name)

    def configure_blocks(self):
        """Configures the root block.

        Combines latent fault injection (SB) with parallel processing of incoming
        SBE (Coverage) and DBE (Split) faults using a SumBlock.
        """
        self.root_block = SumBlock(
            self.name,
            [
                BasicEvent("Sec", FaultType.SB, self.sb_source, is_spfm=False),
                CoverageBlock(
                    "Sec",
                    FaultType.SBE,
                    self.sbe_dc_residual,
                    dc_rate_latent_cL=self.sbe_dc_latent,
                    is_spfm=True,
                ),
                SplitBlock(
                    "Sec_DBE_Split",
                    FaultType.DBE,
                    {
                        FaultType.DBE: self.dbe_to_dbe_p,
                        FaultType.TBE: self.dbe_to_tbe_p,
                    },
                    is_spfm=True,
                ),
            ],
        )
