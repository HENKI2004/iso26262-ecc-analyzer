"""Factory for creating hardware logic blocks from serialized data."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from typing import Any, Type

from ..interfaces import BlockInterface, FaultType
from .basic_event import BasicEvent
from .coverage_block import CoverageBlock
from .pipeline_block import PipelineBlock
from .split_block import SplitBlock
from .sum_block import SumBlock


class BlockFactory:
    """Factory class to reconstruct BlockInterface objects from dictionaries.

    This factory handles the recursive instantiation of complex block trees
    and ensures that serialized data types (like strings) are converted
    back into internal types (like FaultType Enums).
    """

    _REGISTRY: dict[str, Type[BlockInterface]] = {
        "SumBlock": SumBlock,
        "PipelineBlock": PipelineBlock,
        "BasicEvent": BasicEvent,
        "CoverageBlock": CoverageBlock,
        "SplitBlock": SplitBlock,
    }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> BlockInterface:
        """Creates a block instance from a configuration dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing the block
                configuration. Must include a 'type' key.

        Returns:
            BlockInterface: An initialized instance of the specified block.

        Raises:
            ValueError: If the 'type' is unknown or required keys are missing.
        """
        params = data.copy()
        block_type = params.pop("type", None)

        if block_type not in BlockFactory._REGISTRY:
            raise ValueError(f"Unknown block type: {block_type}")

        cls = BlockFactory._REGISTRY[block_type]

        if "sub_blocks" in params:
            params["sub_blocks"] = [BlockFactory.from_dict(b) for b in params["sub_blocks"]]

        fault_keys = ["fault_type", "target_fault", "source_fault", "fault_to_split"]
        for key in fault_keys:
            if key in params and isinstance(params[key], str):
                params[key] = FaultType[params[key]]

        if "distribution_rates" in params:
            params["distribution_rates"] = {FaultType[k]: v for k, v in params["distribution_rates"].items()}

        return cls(**params)
