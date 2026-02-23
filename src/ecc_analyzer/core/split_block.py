"""Distributes FIT rates of a specific fault type across multiple targets."""

# Copyright (c) 2025 Linus Held. All rights reserved.

import sympy

from ..interfaces import BlockInterface, FaultType


class SplitBlock(BlockInterface):
    """Distributes the FIT rate of a specific fault type across multiple other fault types.

    The distribution is based on a defined percentage mapping. This is typically used
    to model how a generic fault (like "DRAM Error") manifests as specific sub-types
    (e.g., SBE, DBE) based on physical probabilities.
    """

    def __init__(
        self,
        name: str,
        fault_to_split: FaultType,
        distribution_rates: dict[FaultType, float],
        is_spfm: bool = True,
    ):
        """Initializes the SplitBlock with a distribution mapping.

        Args:
            name (str): The descriptive name of the split operation.
            fault_to_split (FaultType): The source fault type (Enum) to be distributed.
            distribution_rates (dict[FaultType, float]): Dictionary mapping target
                FaultTypes to their probability (0.0 - 1.0).
            is_spfm (bool, optional): Indicates if this split occurs on the SPFM/residual
                path. Defaults to True.

        Raises:
            ValueError: If the sum of the provided distribution rates exceeds 1.0.
        """
        sum_of_rates = sum(distribution_rates.values())
        if sum_of_rates > 1.0 + 1e-9:
            raise ValueError(f"Sum of distribution rates ({sum_of_rates:.4f}) must not exceed 1.0.")

        self.name = name
        self.fault_to_split = fault_to_split
        self.distribution_rates = distribution_rates
        self.is_spfm = is_spfm

    def compute_fit(self, spfm_rates: dict[FaultType, float], lfm_rates: dict[FaultType, float]) -> tuple[dict[FaultType, float], dict[FaultType, float]]:
        """Transforms the input fault rate dictionaries by redistributing the source fault rate.

        Args:
            spfm_rates (dict[FaultType, float]): Current residual failure rates.
            lfm_rates (dict[FaultType, float]): Current latent failure rates.

        Returns:
            tuple[dict[FaultType, float], dict[FaultType, float]]: A tuple containing:
                - Updated SPFM rates.
                - Updated LFM rates.
        """
        new_spfm = spfm_rates.copy()
        new_lfm = lfm_rates.copy()
        target_dict = new_spfm if self.is_spfm else new_lfm

        if self.fault_to_split in target_dict:
            original_rate = target_dict.pop(self.fault_to_split)
            for target_fault, probability in self.distribution_rates.items():
                split_rate = original_rate * probability
                target_dict[target_fault] = target_dict.get(target_fault, 0.0) + split_rate

        return new_spfm, new_lfm

    def to_dict(self):
        """Serializes the SplitBlock into a dictionary for configuration export.

        Returns:
            dict: A dictionary containing the block type and all parameters
                needed to reconstruct this SplitBlock via the BlockFactory.
        """

        return {
            "type": "SplitBlock",
            "name": self.name,
            "fault_to_split": self.fault_to_split.name,
            "distribution_rates": {fault.name: rate for fault, rate in self.distribution_rates.items()},
            "is_spfm": self.is_spfm,
        }

    def compute_symbolic_fit(self, spfm_exprs, lfm_exprs, mode):
        new_spfm = spfm_exprs.copy()
        new_lfm = lfm_exprs.copy()
        target_dict = new_spfm if self.is_spfm else new_lfm

        if self.fault_to_split in target_dict:
            original_rate = target_dict.pop(self.fault_to_split)
            for target_fault, probability in self.distribution_rates.items():
                p_val = sympy.Symbol(f"p_{self.name}_{target_fault.name}") if mode == "all_vars" else probability
                split_rate = original_rate * p_val
                target_dict[target_fault] = target_dict.get(target_fault, 0) + split_rate

        return new_spfm, new_lfm
