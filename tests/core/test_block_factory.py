import pytest

from ecc_analyzer.core.basic_event import BasicEvent
from ecc_analyzer.core.block_factory import BlockFactory
from ecc_analyzer.core.coverage_block import CoverageBlock
from ecc_analyzer.core.pipeline_block import PipelineBlock
from ecc_analyzer.core.split_block import SplitBlock
from ecc_analyzer.core.sum_block import SumBlock
from ecc_analyzer.interfaces.fault_type import FaultType

# --- Tests for simple blocks ---


def test_from_dict_basic_event():
    """Verify creation of a BasicEvent and its enum conversion."""
    data = {"type": "BasicEvent", "fault_type": "SBE", "rate": 150.0, "is_spfm": True}
    block = BlockFactory.from_dict(data)

    assert isinstance(block, BasicEvent)
    assert block.fault_type == FaultType.SBE
    assert block.lambda_BE == 150.0
    assert block.is_spfm is True


def test_from_dict_coverage_block():
    """Verify creation of a CoverageBlock."""
    data = {"type": "CoverageBlock", "target_fault": "DBE", "dc_rate_c_or_cR": 0.95, "dc_rate_latent_cL": 0.8}
    block = BlockFactory.from_dict(data)

    assert isinstance(block, CoverageBlock)
    assert block.target_fault == FaultType.DBE
    assert block.c_R == 0.95
    assert block.c_L == 0.8


# --- Tests for complex data structures ---


def test_from_dict_split_block_rates():
    """Verify conversion of the distribution_rates dictionary keys from string to enum."""
    data = {"type": "SplitBlock", "name": "DRAM_Split", "fault_to_split": "OTH", "distribution_rates": {"SBE": 0.5, "DBE": 0.5}, "is_spfm": False}
    block = BlockFactory.from_dict(data)

    assert isinstance(block, SplitBlock)
    assert block.fault_to_split == FaultType.OTH
    # The factory must convert dictionary keys from string to FaultType enum
    assert FaultType.SBE in block.distribution_rates
    assert block.distribution_rates[FaultType.SBE] == 0.5


# --- Tests for recursive nesting ---


def test_from_dict_recursive_sum_block():
    """Verify that a SumBlock initializes its sub_blocks recursively."""
    data = {
        "type": "SumBlock",
        "name": "ParallelPath",
        "sub_blocks": [
            {"type": "BasicEvent", "fault_type": "SBE", "rate": 10.0},
            {"type": "PipelineBlock", "name": "NestedPipe", "sub_blocks": [{"type": "BasicEvent", "fault_type": "DBE", "rate": 5.0}]},
        ],
    }
    block = BlockFactory.from_dict(data)

    assert isinstance(block, SumBlock)
    assert len(block.sub_blocks) == 2
    assert isinstance(block.sub_blocks[0], BasicEvent)
    assert isinstance(block.sub_blocks[1], PipelineBlock)
    assert isinstance(block.sub_blocks[1].sub_blocks[0], BasicEvent)


# --- Tests for error handling ---


def test_from_dict_unknown_type():
    """Verify that unknown block types raise a ValueError."""
    with pytest.raises(ValueError, match="Unknown block type: FakeBlock"):
        BlockFactory.from_dict({"type": "FakeBlock"})


def test_from_dict_missing_type():
    """Verify behavior when the 'type' key is missing."""
    with pytest.raises(ValueError, match="Unknown block type: None"):
        BlockFactory.from_dict({"name": "NoType"})
