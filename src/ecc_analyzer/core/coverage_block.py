"""Applies diagnostic coverage (DC) to fault rates."""

# Copyright (c) 2025 Linus Held. All rights reserved.

import sympy

from ..interfaces import BlockInterface, FaultType


class CoverageBlock(BlockInterface):
    """Applies diagnostic coverage (DC) to a fault type.

    Splits FIT rates into residual and latent components based on the defined
    coverage values (c_R, c_L).
    """

    def __init__(
        self,
        name: str,
        target_fault: FaultType,
        dc_rate_c_or_cR: float,
        dc_rate_latent_cL: float,
        is_spfm: bool = True,
    ):
        """Initializes the CoverageBlock with specific diagnostic coverage parameters.

        Args:
            target_fault (FaultType): The fault type (Enum) to which coverage is applied.
            dc_rate_c_or_cR (float): The diagnostic coverage for residual faults
                (typically denoted as K_DC or c_R).
            dc_rate_latent_cL (Optional[float]): Optional specific coverage for latent
                faults (c_L). If None, standard ISO 26262 logic (1 - c_R) is assumed.
            is_spfm (bool, optional): Indicates if this block processes the SPFM/residual
                path. Defaults to True.
        """
        self.name = name
        self.target_fault = target_fault
        self.is_spfm = is_spfm
        self.c_R = dc_rate_c_or_cR
        self.c_L = dc_rate_latent_cL

    def compute_fit(self, spfm_rates: dict[FaultType, float], lfm_rates: dict[FaultType, float]) -> tuple[dict[FaultType, float], dict[FaultType, float]]:
        """Transforms the input fault rate dictionaries by applying diagnostic coverage logic.

        Args:
            spfm_rates (dict[FaultType, float]): Current residual failure rates.
            lfm_rates (dict[FaultType, float]): Current latent failure rates.

        Returns:
            tuple[dict[FaultType, float], dict[FaultType, float]]: A tuple containing:
                - Updated SPFM rates dictionary.
                - Updated LFM rates dictionary.
        """
        new_spfm = spfm_rates.copy()
        new_lfm = lfm_rates.copy()

        if self.is_spfm:
            if self.target_fault in new_spfm:
                lambda_in = new_spfm.pop(self.target_fault)
                lambda_rf = lambda_in * (1.0 - self.c_R)
                if lambda_rf > 0:
                    new_spfm[self.target_fault] = new_spfm.get(self.target_fault, 0.0) + lambda_rf
                lambda_mpf_l = lambda_in * (1.0 - self.c_L)
                if lambda_mpf_l > 0:
                    new_lfm[self.target_fault] = new_lfm.get(self.target_fault, 0.0) + lambda_mpf_l
        else:
            if self.target_fault in new_lfm:
                lambda_in = new_lfm.pop(self.target_fault)
                lambda_rem = lambda_in * (1.0 - self.c_L)
                if lambda_rem > 0:
                    new_lfm[self.target_fault] = lambda_rem

        return new_spfm, new_lfm

    def to_dict(self):
        """Serializes the CoverageBlock into a dictionary for configuration export.

        Returns:
            dict: A dictionary containing the block type and all parameters
                needed to reconstruct this CoverageBlock via the BlockFactory.
        """

        return {"type": "CoverageBlock", "target_fault": self.target_fault.name, "dc_rate_c_or_cR": self.c_R, "dc_rate_latent_cL": self.c_L, "is_spfm": self.is_spfm}

    def compute_symbolic_fit(self, spfm_exprs, lfm_exprs, mode):
        new_spfm = spfm_exprs.copy()
        new_lfm = lfm_exprs.copy()

        if mode in ["all_vars", "coverage_vars"]:
            c_r_val = sympy.Symbol(f"c_R_{self.name}_{self.target_fault.name}")
            c_l_val = sympy.Symbol(f"c_L_{self.name}_{self.target_fault.name}")
        else:
            c_r_val = self.c_R
            c_l_val = self.c_L

        if self.is_spfm:
            if self.target_fault in new_spfm:
                lambda_in = new_spfm.pop(self.target_fault)
                new_spfm[self.target_fault] = new_spfm.get(self.target_fault, 0) + lambda_in * (1.0 - c_r_val)
                new_lfm[self.target_fault] = new_lfm.get(self.target_fault, 0) + lambda_in * (1.0 - c_l_val)
        else:
            if self.target_fault in new_lfm:
                lambda_in = new_lfm.pop(self.target_fault)
                new_lfm[self.target_fault] = lambda_in * (1.0 - c_l_val)

        return new_spfm, new_lfm
