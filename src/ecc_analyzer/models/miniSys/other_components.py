from ...core import Base, BasicEvent, PipelineBlock
from ...interfaces import FaultType


class OtherComponents(Base):
    def __init__(self, name: str, total_fit: float, other_fit: float):
        self.total_other_fit = other_fit
        super().__init__(name, total_fit)

    def configure_blocks(self):
        self.root_block = PipelineBlock(
            self.name,
            [BasicEvent("ALL_OTHER", FaultType.OTH, self.total_other_fit, is_spfm=True)],
        )
