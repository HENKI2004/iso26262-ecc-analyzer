"""Evaluates final system metrics and determines the achieved ASIL level."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from typing import Any

from ..interfaces import FaultType


class AsilBlock:
    """Evaluates final system metrics and determines the achieved ASIL level.

    Calculates Single-Point Fault Metric (SPFM) and Latent Fault Metric (LFM)
    according to ISO 26262 requirements.
    """

    # Standardized ASIL requirements
    # Format: [Min SPFM, Min LFM, Max Residual FIT]
    ASIL_REQUIREMENTS = {
        "D": [0.99, 0.90, 10.0],
        "C": [0.97, 0.80, 100.0],
        "B": [0.90, 0.60, 100.0],
        "A": [0.00, 0.00, 1000.0],
    }

    def __init__(self, name: str):
        """Initializes the ASIL calculation block.

        Args:
            name (str): The descriptive name of the calculation block.
        """
        self.name = name

    def _determine_asil(self, spfm: float, lfm: float, lambda_rf_sum: float) -> str:
        """Determines the achieved ASIL level based on calculated metrics.

        Args:
            spfm (float): Single-Point Fault Metric value (0.0 to 1.0).
            lfm (float): Latent Fault Metric value (0.0 to 1.0).
            lambda_rf_sum (float): Total sum of residual FIT rates.

        Returns:
            str: A string representing the achieved ASIL level (e.g., "ASIL D")
            or "QM" (Quality Management).
        """
        for asil_level in ["D", "C", "B"]:
            req = self.ASIL_REQUIREMENTS[asil_level]
            spfm_min, lfm_min, rf_max = req
            if spfm >= spfm_min and lfm >= lfm_min and lambda_rf_sum < rf_max:
                return f"ASIL {asil_level}"

        if lambda_rf_sum < self.ASIL_REQUIREMENTS["A"][2]:
            return "ASIL A"

        return "QM (Quality Management)"

    def compute_metrics(
        self,
        lambda_total: float,
        final_spfm_dict: dict[FaultType, float],
        final_lfm_dict: dict[FaultType, float],
    ) -> dict[str, Any]:
        """Calculates final ISO 26262 metrics using result dictionaries.

        Args:
            lambda_total (float): The total FIT rate of the entire system.
            final_spfm_dict (dict[FaultType, float]): Dictionary containing final
                residual and dangerous FIT rates.
            final_lfm_dict (dict[FaultType, float]): Dictionary containing final
                latent FIT rates.

        Returns:
            dict[str, Any]: A dictionary containing:
                - "SPFM" (float): Single-Point Fault Metric.
                - "LFM" (float): Latent Fault Metric.
                - "Lambda_RF_Sum" (float): Residual FIT Rate Sum.
                - "ASIL_Achieved" (str): The determined ASIL level.
        """
        lambda_dangerous_sum = sum(final_spfm_dict.values())
        lambda_latent_sum = sum(final_lfm_dict.values())
        lambda_rf_sum = lambda_dangerous_sum

        spfm = 0.0
        lfm = 0.0

        if lambda_total > 0:
            spfm = 1.0 - (lambda_dangerous_sum / lambda_total)

        lambda_safe_and_covered = lambda_total - lambda_dangerous_sum

        if lambda_safe_and_covered > 0:
            lfm = 1.0 - (lambda_latent_sum / lambda_safe_and_covered)

        achieved_asil = self._determine_asil(spfm, lfm, lambda_rf_sum)

        return {"SPFM": spfm, "LFM": lfm, "Lambda_RF_Sum": lambda_rf_sum, "Lambda_Latent": lambda_latent_sum, "ASIL_Achieved": achieved_asil, "total_fit": lambda_total}
