"""Top-level system model for the LPDDR5 hardware architecture."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import PipelineBlock, SumBlock
from ...system_base import SystemBase
from .link_ecc import LinkEcc
from .other_components import OtherComponents

# from .sec_ded1 import SecDed1
# from .sec_ded2 import SecDed2
from .sec_ded import SecDed
from .sec_ded_trim import SecDedTrim


class Lpddr5System(SystemBase):
    """Coordinates the connection of all sub-components and defines the overall system layout for LPDDR5."""

    def __init__(self, name, total_fit, other_fit):
        self.other_fit = other_fit
        super().__init__(name, total_fit)

    def configure_system(self):
        """Defines the hierarchical structure of the LPDDR5 system.

        Constructs the main DRAM processing chain (Sources -> SEC -> TRIM -> BUS -> LINK -> SEC-DED -> TRIM)
        and merges it with other hardware components.
        """
        main_chain = PipelineBlock(
            "DRAM_Path",
            [
                LinkEcc("LINK-ECC", self.total_fit),
                SecDed("SEC-DED", self.total_fit),
                SecDedTrim("SEC-DED-TRIM", self.total_fit),
            ],
        )

        self.system_layout = SumBlock(self.name, [main_chain, OtherComponents("Other_HW", self.total_fit, self.other_fit)])
