from ...core import SumBlock
from ...system_base import SystemBase
from .component import DRAMComponent
from .other_components import OtherComponents


class MinimalSystem(SystemBase):
    def __init__(self, name, total_fit, other_fit):
        self.other_fit = other_fit
        super().__init__(name, total_fit)

    def configure_system(self):
        dram_path = DRAMComponent("DRAM_Unit", self.total_fit)
        other_hw = OtherComponents("Other_HW", self.total_fit, self.other_fit)

        self.system_layout = SumBlock(self.name, [dram_path, other_hw])
