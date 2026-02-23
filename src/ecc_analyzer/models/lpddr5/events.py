"""Primary failure rate source component for LPDDR5 DRAM."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, SumBlock
from ...interfaces import FaultType


class Events(Base):
    """Initializes the baseline DRAM failure rates for LPDDR5.

    This module acts as a primary source for SBE, DBE, MBE, and WD faults.
    As a pure source component, it uses a SumBlock to inject all rates in parallel.
    """

    def __init__(self, name: str):
        """Initializes the fault rates based on a baseline DRAM FIT value.

        Args:
            name (str): The descriptive name of the component.
        """
        dram_fit = 2300.0

        self.fault_sbe = 0.7 * dram_fit
        self.fault_dbe = 0.0748 * dram_fit
        self.fault_mbe = 0.0748 * dram_fit
        self.fault_wd = 0.0748 * dram_fit

        super().__init__(name)

    def configure_blocks(self):
        """Configures the internal block structure by injecting failure rates as basic events.

        Uses a SumBlock as these faults occur independently and in parallel on the hardware level.
        """
        self.root_block = SumBlock(
            self.name,
            [
                BasicEvent("Events", FaultType.SBE, self.fault_sbe, is_spfm=True),
                BasicEvent("Events", FaultType.DBE, self.fault_dbe, is_spfm=True),
                BasicEvent("Events", FaultType.MBE, self.fault_mbe, is_spfm=True),
                BasicEvent("Events", FaultType.WD, self.fault_wd, is_spfm=True),
            ],
        )
