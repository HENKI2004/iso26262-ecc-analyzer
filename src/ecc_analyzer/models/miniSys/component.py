from ...core import Base, BasicEvent, CoverageBlock, PipelineBlock, SumBlock
from ...interfaces import FaultType


class DRAMComponent(Base):
    """Encapsulates the internal safety logic of a DRAM unit."""

    def __init__(self, name: str, total_fit: float):
        self.sbe_rate = 40.0
        self.mbe_rate = 5.0
        super().__init__(name, total_fit)

    def configure_blocks(self):
        sbe_chain = PipelineBlock("SBE_Path", [BasicEvent("SBE_Source", FaultType.SBE, self.sbe_rate), CoverageBlock("ECC_Layer", FaultType.SBE, 1.0, 1.0)])
        mbe_event = BasicEvent("MBE_Source", FaultType.MBE, self.mbe_rate)
        self.root_block = SumBlock(self.name, [sbe_chain, mbe_event])
