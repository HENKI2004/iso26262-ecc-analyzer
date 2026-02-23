"""Component representing miscellaneous hardware parts with fixed FIT rates (LPDDR5)."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, SumBlock
from ...interfaces import FaultType


class OtherComponents(Base):
    """Component representing miscellaneous hardware parts that contribute a fixed FIT rate.

    This module encapsulates all non-DRAM components (e.g., peripheral logic) into a
    single source injection block to simplify the top-level model.
    """

    def __init__(self, name: str):
        """Initializes the component and sets the constant source FIT rate.

        Args:
            name (str): The descriptive name of the component.
        """
        self.other_rf_source = 9.5

        super().__init__(name)

    def configure_blocks(self):
        """Configures the root block to inject the FIT rate.

        Uses a SumBlock as the base container for the fault source (BasicEvent).
        The fault is injected into the residual path (is_spfm=True).
        """
        self.root_block = SumBlock(
            self.name,
            [
                BasicEvent("OTH", FaultType.OTH, self.other_rf_source, is_spfm=True),
            ],
        )
