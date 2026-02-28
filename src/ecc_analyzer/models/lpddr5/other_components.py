"""Component representing miscellaneous hardware parts with fixed FIT rates (LPDDR5)."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, CoverageBlock, PipelineBlock, SplitBlock
from ...interfaces import FaultType


class OtherComponents(Base):
    """Component representing miscellaneous hardware parts that contribute a fixed FIT rate.

    This module encapsulates all non-DRAM components (e.g., peripheral logic) into a
    single source injection block to simplify the top-level model.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the component and sets the constant source FIT rate.

        Args:
            name (str): The descriptive name of the component.
        """
        self.total_other_fit = total_fit * 0.4523809524
        super().__init__(name, total_fit)

    def configure_blocks(self):
        # Wir bauen die Kette exakt nach dem SystemC Vorbild nach
        self.root_block = PipelineBlock(
            self.name,
            [
                BasicEvent("ALL_OTHER", FaultType.OTH, self.total_other_fit, is_spfm=True),
                SplitBlock("OTHER_SPLIT", FaultType.OTH, {FaultType.OTH: 0.5}, is_spfm=True),
                CoverageBlock("OTHER_COV", FaultType.OTH, 0.99, 0.01, is_spfm=True),
                CoverageBlock("OTHER_COV_LAT", FaultType.OTH, 1.0, 1.0, is_spfm=False),
            ],
        )
