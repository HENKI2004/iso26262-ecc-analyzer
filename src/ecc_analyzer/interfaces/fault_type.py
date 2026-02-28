"""Defines the Faulttypes which are possible"""

# Copyright (c) 2025 Linus Held. All rights reserved.

from enum import Enum, auto


class FaultType(Enum):
    """
    Enumeration of supported fault types within the safety model.
    Each member represents a specific failure mode used for FIT rate calculations and visualization.
    """

    SBE = auto()
    DBE = auto()
    TBE = auto()
    MBE = auto()
    WD = auto()
    AZ = auto()
    SB = auto()
    SDB = auto()
    OTH = auto()
    SBE_IF = auto()
    LB = auto()
