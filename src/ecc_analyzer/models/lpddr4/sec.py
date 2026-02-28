"""Component for Single Error Correction (SEC) in LPDDR4 architectures."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, CoverageBlock, SplitBlock, SumBlock
from ...interfaces import FaultType


class Sec(Base):
    """Component for Single Error Correction (SEC) in LPDDR4 architectures.

    This module handles SBE coverage and redistributes DBE failure rates into TBEs.
    It uses a PipelineBlock to ensure that local sources are added before
    diagnostic coverage and split operations are applied.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the SEC component with specific diagnostic coverage and failure rates.

        Args:
            name (str): The descriptive name of the component.
        """
        self.sec_ecc_dc = 1.0
        self.dbe_to_dbe_p = 0.83
        self.dbe_to_tbe_p = 0.17

        self.sb_source = 0.1
        self.dbe_source = 172.0

        super().__init__(name, total_fit)

    def configure_blocks(self):
        """Configures the internal block structure as a sequential pipeline.

        This ensures fault sources are injected first, followed by coverage application
        and final rate redistribution.
        """
        self.root_block = SumBlock(
            self.name,
            [
                BasicEvent("sec", FaultType.SB, self.sb_source, is_spfm=False),
                # BasicEvent("sec", FaultType.DBE, self.dbe_source, is_spfm=False),
                CoverageBlock("sec", FaultType.SBE, self.sec_ecc_dc, 0),
                SplitBlock(
                    "DBE_to_TBE_Split",
                    FaultType.DBE,
                    {
                        FaultType.DBE: self.dbe_to_dbe_p,
                        FaultType.TBE: self.dbe_to_tbe_p,
                    },
                    is_spfm=True,
                ),
            ],
        )
