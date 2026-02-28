"""Top-level system model for the LPDDR4 hardware architecture."""

from ...core import PipelineBlock, SumBlock
from ...system_base import SystemBase
from .bus_trim import BusTrim
from .dram_trim import DramTrim
from .events import Events
from .other_components import OtherComponents
from .sec import Sec
from .sec_ded import SecDed
from .sec_ded_trim import SecDedTrim


class Lpddr4System(SystemBase):
    """
    Coordinates the connection of all sub-components and defines the overall system layout.
    """

    def configure_system(self):
        """
        Defines the hierarchical structure of the LPDDR4 system.
        Constructs the main DRAM processing chain and merges it with other hardware components.
        """
        main_chain = PipelineBlock(
            "DRAM_Path",
            [
                Events("Source", self.total_fit),
                Sec("SEC", self.total_fit),
                DramTrim("TRIM", self.total_fit),
                BusTrim("BUS", self.total_fit),
                SecDed("SEC-DED", self.total_fit),
                SecDedTrim("SEC-DED-TRIM", self.total_fit),
            ],
        )

        self.system_layout = SumBlock(self.name, [main_chain, OtherComponents("Other_HW", self.total_fit)])
