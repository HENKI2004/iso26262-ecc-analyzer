# ECC Analyzer

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Standard](https://img.shields.io/badge/ISO-26262)

**ECC Analyzer** is a modular safety analysis framework designed to calculate failure rates (FIT), diagnostic coverage, and architectural metrics (SPFM, LFM) for semiconductor memory systems (e.g., LPDDR4/5).

It combines strict mathematical modeling with automated architectural visualization using Graphviz.

## Features

* **ISO 26262 Metrics:** Automated calculation of Single-Point Fault Metric (SPFM) and Latent Fault Metric (LFM).
* **Modular Architecture:** Build complex hardware models using reusable blocks (`SumBlock`, `PipelineBlock`, `SplitBlock`).
* **Visual Observer:** Automatically generates architectural diagrams (PDF) reflecting the exact logic of the safety model.
* **Traceability:** Faults are tracked from the source (Basic Events) through ECC/logic layers to the final output.

## Installation

Prerequisites:
* Python 3.9 or higher
* [Graphviz](https://graphviz.org/download/) installed on your system (required for visualization).

### For Users
Install the package directly from the source:

```bash
pip install .
```

# For Developers

Install in editable mode with development tools (linting, testing):

```bash

pip install -e .[dev]

```

## Usage

### Running the LPDDR4 Analysis

The project includes a pre-configured model for an LPDDR4 system. You can run the analysis script directly:

```bash

python main.py

```

### Creating a Custom Model

You can define your own safety architecture by subclassing SystemBase:

```python

from ecc_analyzer.core import PipelineBlock, SumBlock, BasicEvent
from ecc_analyzer.system_base import SystemBase

class MySafetySystem(SystemBase):
    def configure_system(self):
        # Define your logic chain
        self.system_layout = PipelineBlock("MyPath", [
            BasicEvent("Source_SBE", rate=100.0),
            # Add more blocks here...
        ])

# Run analysis
system = MySafetySystem("MyChip", total_fit=1000.0)
metrics = system.run_analysis()
print(metrics)
```
## Architecture

The project follows the **Observer Pattern** to decouple calculation from visualization:

* `core/`: Contains the logic blocks (`SumBlock`, `SplitBlock`) that handle FIT rate math.

* `models/`: Contains specific hardware implementations (e.g., LPDDR4).

* `visualization/`: The `SafetyVisualizer` observes the logic blocks and draws the Graphviz diagram.

## Contributing
1. Install dependencies: `pip install -e .[dev]`

2. Format code: `ruff format .`

3. Run checks: `ruff check .`

# License
Copyright (c) 2025 Linus Held. Licensed under the MIT License.
