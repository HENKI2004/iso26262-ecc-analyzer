"""Orchestrates the safety analysis and coordinates visualization via observers."""

# Copyright (c) 2025 Linus Held. All rights reserved.

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

import sympy
import yaml

from .core import AsilBlock, BlockFactory, ObservableBlock
from .visualization import SafetyVisualizer


class SystemBase(ABC):
    """Abstract base class for a safety system model.

    It manages the system layout, triggers FIT rate calculations, and
    handles the generation of architectural visualizations.
    """

    def __init__(self, name: str, total_fit: float):
        """Initializes the system orchestrator.

        Args:
            name (str): The descriptive name of the system (e.g., "LPDDR4_System").
            total_fit (float): The total FIT rate used as the baseline for metric calculations.
        """
        self.name = name
        self.total_fit = total_fit
        self.system_layout = None
        self.asil_block = AsilBlock("Final_Evaluation")
        self.configure_system()

    @abstractmethod
    def configure_system(self):
        """Abstract method to define the internal hardware structure.

        Must be implemented by subclasses to set the `self.system_layout`.
        """
        pass

    def run_analysis(self) -> dict[str, Any]:
        """Performs a pure mathematical FIT calculation across the system.

        No visualization is triggered during this call.

        Returns:
            dict[str, Any]: A dictionary containing calculated metrics (SPFM, LFM, ASIL level).

        Raises:
            ValueError: If `configure_system` has not set a valid system layout.
        """
        if not self.system_layout:
            raise ValueError("System layout is not configured.")

        def get_actual_total_fit(block):
            total = 0.0
            if hasattr(block, "lambda_BE"):
                total += block.lambda_BE
            if hasattr(block, "sub_blocks"):
                for sub in block.sub_blocks:
                    total += get_actual_total_fit(sub)
            if hasattr(block, "root_block") and block.root_block:
                total += get_actual_total_fit(block.root_block)
            return total

        self.total_fit = get_actual_total_fit(self.system_layout)

        final_spfm, final_lfm = self.system_layout.compute_fit({}, {})

        return self.asil_block.compute_metrics(self.total_fit, final_spfm, final_lfm)

    def generate_pdf(self, filename: Optional[str] = None) -> dict[str, Any]:
        """Executes the analysis while simultaneously generating a PDF visualization.

        Uses the Observer Pattern to decouple logic from Graphviz commands.

        Args:
            filename (Optional[str]): Optional name for the output file.
                Defaults to "output_<system_name>".

        Returns:
            dict[str, Any]: The final system metrics dictionary.
        """
        if filename is None:
            filename = f"output_{self.name}"

        visualizer = SafetyVisualizer(self.name)

        observable_layout = ObservableBlock(self.system_layout)
        observable_layout.attach(visualizer)

        final_spfm, final_lfm, last_ports = observable_layout.compute_fit({}, {}, {})

        visualizer.on_block_computed(
            self.asil_block,
            last_ports,
            final_spfm,
            final_lfm,
            final_spfm,
            final_lfm,
        )

        visualizer.render(filename)

        return self.asil_block.compute_metrics(self.total_fit, final_spfm, final_lfm)

    def save_to_yaml(self, file_path: str):
        """Exports the current system layout to a YAML file.

        Args:
            file_path (str): The destination path for the YAML file.
        """
        config = self.system_layout.to_dict()
        with open(file_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def load_from_yaml(self, file_path: str):
        """Loads a system layout from a YAML file and reconstructs the block tree.

        Args:
            file_path (str): The path to the configuration file.
        """
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        self.system_layout = BlockFactory.from_dict(data)

    def save_to_json(self, file_path: str):
        """Exports the current system layout to a JSON file.

        Args:
            file_path (str): The destination path for the JSON file.
        """
        config = self.system_layout.to_dict()
        with open(file_path, "w") as f:
            json.dump(config, f, indent=4)

    def load_from_json(self, file_path: str):
        """Loads a system layout from a JSON file and reconstructs the block tree.

        Args:
            file_path (str): The path to the configuration file.
        """
        with open(file_path, "r") as f:
            data = json.load(f)
        self.system_layout = BlockFactory.from_dict(data)

    def get_symbolic_metrics(self, mode: str = "be_vars") -> dict[str, sympy.Expr]:
        """

        Args:
            mode:
                "all_vars": Alles (FIT-Raten, DCs, Splits) wird als Variable dargestellt.
                "be_vars": Nur FIT-Raten der Basic Events sind Variablen, DCs sind Zahlen.
                "coverage_vars": FIT-Raten sind Zahlen, nur Diagnostic Coverages (DCs) sind Variablen.
                "numeric": Alle Werte sind eingesetzt (Formel-Check).
        """
        be_symbols = []

        def get_actual_total_fit(block):
            total = 0.0
            if hasattr(block, "lambda_BE"):
                total += block.lambda_BE
            if hasattr(block, "sub_blocks"):
                for sub in block.sub_blocks:
                    total += get_actual_total_fit(sub)
            if hasattr(block, "root_block") and block.root_block:
                total += get_actual_total_fit(block.root_block)
            return total

        self.total_fit = get_actual_total_fit(self.system_layout)

        final_spfm_exprs, final_lfm_exprs = self.system_layout.compute_symbolic_fit({}, {}, mode)

        lambda_rf_sum = sympy.Add(*final_spfm_exprs.values()) if final_spfm_exprs else sympy.Integer(0)

        lambda_latent_sum = sympy.Add(*final_lfm_exprs.values()) if final_lfm_exprs else sympy.Integer(0)

        spfm_formula = 1 - (lambda_rf_sum / self.total_fit)

        denominator_lfm = self.total_fit - lambda_rf_sum
        lfm_formula = 1 - (lambda_latent_sum / denominator_lfm) if denominator_lfm != 0 else sympy.Integer(0)

        return {"mode": mode, "SPFM": sympy.simplify(spfm_formula), "LFM": sympy.simplify(lfm_formula), "Lambda_RF": sympy.simplify(lambda_rf_sum), "Lambda_Total": sympy.simplify(self.total_fit)}
