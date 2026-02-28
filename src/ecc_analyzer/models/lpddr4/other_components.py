"""Component representing miscellaneous hardware parts with fixed FIT rates (LPDDR4)."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from ...core import Base, BasicEvent, CoverageBlock, PipelineBlock, SplitBlock
from ...interfaces import FaultType


class OtherComponents(Base):
    """Component representing miscellaneous hardware parts that contribute a fixed FIT rate.

    This module encapsulates all non-DRAM components into a single source injection
    block to simplify the top-level model.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the component and sets the constant source FIT rate.

        Args:
            name (str): The descriptive name of the component.
        """
        self.total_other_fit = 1920.0
        super().__init__(name, total_fit)

    def configure_blocks(self):
        # Wir bauen die Kette exakt nach dem SystemC Vorbild nach
        self.root_block = PipelineBlock(
            self.name,
            [
                # 1. Die volle FIT-Quelle (bevor irgendwas abgezogen wird)
                BasicEvent("ALL_OTHER", FaultType.OTH, self.total_other_fit, is_spfm=True),
                # 2. Der Split: 50% werden als Safe Faults deklariert (fallen weg)
                SplitBlock("OTHER_SPLIT", FaultType.OTH, {FaultType.OTH: 0.5}, is_spfm=True),
                # 3. Erste Coverage: 90% Diagnostic Coverage (DC)
                #    lc (Latent Coverage) ist im C++ Code als 1.0 - 0.9 = 0.1 definiert
                CoverageBlock("OTHER_COV", FaultType.OTH, 0.9, 0.1, is_spfm=True),
                # 4. Zweite Coverage: Sie deckt die verbleibenden latenten Fehler zu 100% ab
                #    Im C++ Code sorgt other_cov_lat mit dc=1.0 dafür, dass OTHER_LAT = 0 wird
                CoverageBlock("OTHER_COV_LAT", FaultType.OTH, 1.0, 1.0, is_spfm=False),
            ],
        )
