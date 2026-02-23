"""Component for Single Error Correction and Double Error Detection (SEC-DED) in LPDDR5."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, CoverageBlock, PipelineBlock, SplitBlock, SumBlock
from ...interfaces import FaultType


class SecDed(Base):
    """Component for Single Error Correction and Double Error Detection (SEC-DED).

    This module handles the diagnostic coverage for multiple fault types (SBE, DBE, TBE, MBE)
    and manages the transformation of Triple Bit Errors (TBE) into Multi Bit Errors (MBE).
    """

    def __init__(self, name: str):
        """Initializes the SEC-DED component with coverage and source parameters.

        Args:
            name (str): The descriptive name of the component.
        """

        self.sbe_dc = 1.0
        self.dbe_dc = 1.0
        self.mbe_dc = 0.5
        self.tbe_dc = 1.0

        self.tbe_split_to_mbe = 0.56

        self.lfm_sbe_dc = 1.0
        self.lfm_dbe_dc = 1.0

        self.sdb_source = 0.1

        super().__init__(name)

    def configure_blocks(self):
        """Configures the block structure.

        Uses a SumBlock to combine the latent fault source (SDB) with the main
        processing pipeline (Split & Coverage).
        """
        spfm_pipeline = PipelineBlock(
            "SEC_DED_Processing",
            [
                SplitBlock(
                    "Sec_ded_TBE_to_MBE_Split",
                    FaultType.TBE,
                    {
                        FaultType.MBE: self.tbe_split_to_mbe,
                        FaultType.TBE: 1.0 - self.tbe_split_to_mbe,
                    },
                    is_spfm=True,
                ),
                CoverageBlock(
                    "Sec_ded",
                    FaultType.SBE,
                    self.sbe_dc,
                    dc_rate_latent_cL=self.lfm_sbe_dc,
                    is_spfm=True,
                ),
                CoverageBlock(
                    "Sec_ded",
                    FaultType.DBE,
                    self.dbe_dc,
                    dc_rate_latent_cL=self.lfm_dbe_dc,
                    is_spfm=True,
                ),
                CoverageBlock("Sec_ded", FaultType.TBE, self.tbe_dc, is_spfm=True),
                CoverageBlock("Sec_ded", FaultType.MBE, self.mbe_dc, is_spfm=True),
            ],
        )

        self.root_block = SumBlock(
            self.name,
            [
                spfm_pipeline,
                BasicEvent("Sec_ded", FaultType.SDB, self.sdb_source, is_spfm=False),
            ],
        )
