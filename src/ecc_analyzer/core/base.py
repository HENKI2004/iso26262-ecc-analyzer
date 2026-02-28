"""Abstract base class for hardware components acting as logic containers."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from abc import ABC, abstractmethod
from typing import Optional

from ..interfaces import BlockInterface, FaultType


class Base(BlockInterface, ABC):
    """Abstract base class for hardware components.

    Provides a structured way to define internal logic hierarchies by wrapping
    complex logic into a single modular unit.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the component and triggers the internal block configuration.

        Args:
            name (str): The descriptive name of the hardware component.
        """
        self.name = name
        self.root_block: Optional[BlockInterface] = None
        self.total_fit = total_fit
        self.configure_blocks()

    @abstractmethod
    def configure_blocks(self):
        """Abstract method to define the internal logic structure (root block).

        Must be implemented by subclasses to specify the internal tree of blocks
        (e.g., using SumBlock, PipelineBlock).
        """
        pass

    def compute_fit(self, spfm_rates: dict[FaultType, float], lfm_rates: dict[FaultType, float]) -> tuple[dict[FaultType, float], dict[FaultType, float]]:
        """Delegates the FIT rate transformation to the internal root block.

        This allows the component to be treated as a single modular unit within the system,
        hiding its internal complexity.

        Args:
            spfm_rates (dict[FaultType, float]): Current residual failure rates.
            lfm_rates (dict[FaultType, float]): Current latent failure rates.

        Returns:
            tuple[dict[FaultType, float], dict[FaultType, float]]: Updated FIT rates
            processed by the internal root block.
        """
        if self.root_block is None:
            return spfm_rates.copy(), lfm_rates.copy()

        return self.root_block.compute_fit(spfm_rates, lfm_rates)

    def to_dict(self) -> dict:
        """Serializes the component by delegating to its internal root block."""
        return {"type": self.__class__.__name__, "name": self.name, "root_block": self.root_block.to_dict() if self.root_block else None}

    def compute_symbolic_fit(self, spfm_exprs, lfm_exprs, mode):
        return self.root_block.compute_symbolic_fit(spfm_exprs, lfm_exprs, mode)
