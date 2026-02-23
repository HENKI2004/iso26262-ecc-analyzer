"""Defines the contract for all logic blocks in the safety analysis."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from abc import ABC, abstractmethod

import sympy

from .fault_type import FaultType


class BlockInterface(ABC):
    """Abstract interface defining the mandatory structure for all logic blocks.

    Every block in the system must implement this interface to ensure modularity
    and nesting capabilities within the safety analysis.
    """

    @abstractmethod
    def compute_fit(self, spfm_rates: dict[FaultType, float], lfm_rates: dict[FaultType, float]) -> tuple[dict[FaultType, float], dict[FaultType, float]]:
        """Transforms the input fault rate dictionaries according to the block's specific logic.

        Args:
            spfm_rates (dict[FaultType, float]): Dictionary mapping fault types to
                their current residual (SPFM) failure rates (FIT).
            lfm_rates (dict[FaultType, float]): Dictionary mapping fault types to
                their current latent (LFM) failure rates (FIT).

        Returns:
            tuple[dict[FaultType, float], dict[FaultType, float]]: A tuple containing:
                - Updated SPFM rates dictionary.
                - Updated LFM rates dictionary.
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """
        crates a suitable dictionary for the block

        Returns:
            dict: the created dictionary which represents the block
        """
        pass

    @abstractmethod
    def compute_symbolic_fit(self, spfm_exprs: dict[FaultType, sympy.Expr], lfm_exprs: dict[FaultType, sympy.Expr], mode: str) -> tuple[dict[FaultType, sympy.Expr], dict[FaultType, sympy.Expr]]:
        pass
