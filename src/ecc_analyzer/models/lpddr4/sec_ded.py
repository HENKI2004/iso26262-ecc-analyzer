"""Component for Single Error Correction and Double Error Detection (SEC-DED) in LPDDR4."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, CoverageBlock, PipelineBlock, SplitBlock, SumBlock
from ...interfaces import FaultType


class SecDed(Base):
    """Component for Single Error Correction and Double Error Detection (SEC-DED).

    This module manages diagnostic coverage for multiple fault types and handles
    transformations between failure modes (e.g., TBE -> MBE).
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the SEC-DED component with specific diagnostic coverage and source parameters.

        Args:
            name (str): The descriptive name of the component.
        """
        self.sbe_dc = 1.0
        self.dbe_dc = 1.0
        self.mbe_dc = 0.5
        self.tbe_dc = 1

        self.tbe_split_to_mbe = 0.56

        self.lfm_sbe_dc = 1.0
        self.lfm_dbe_dc = 1.0

        self.sdb_source = 0.1

        super().__init__(name, total_fit)

    def configure_blocks(self):
        """Configures the internal block structure as a sum block."""
        self.root_block = SumBlock(
            self.name,
            [
                BasicEvent("sec_dec", FaultType.SDB, self.sdb_source, is_spfm=False),
                CoverageBlock("sec_dec", FaultType.SBE, 1 - self.lfm_sbe_dc, self.lfm_sbe_dc, is_spfm=False),
                CoverageBlock("sec_dec", FaultType.DBE, 1 - self.lfm_dbe_dc, self.lfm_dbe_dc, is_spfm=False),
                PipelineBlock(
                    "test",
                    [
                        SplitBlock(
                            "sec_ded_tbe_split_to_mbe",
                            FaultType.TBE,
                            {
                                FaultType.TBE: 1 - self.tbe_split_to_mbe,
                                FaultType.MBE: self.tbe_split_to_mbe,
                            },
                        ),
                        CoverageBlock("sec_dec", FaultType.TBE, self.tbe_dc, 0.0),
                    ],
                ),
                CoverageBlock("sec_dec", FaultType.SBE, self.sbe_dc, 0.0),
                CoverageBlock("sec_dec", FaultType.DBE, self.dbe_dc, 0.0),
                CoverageBlock("sec_dec", FaultType.MBE, self.mbe_dc, self.mbe_dc),
            ],
        )
