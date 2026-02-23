"""Implementation of the Graphviz-based safety observer."""

# Copyright (c) 2025 Linus Held. All rights reserved.

from typing import Any, Optional, TypeAlias

from graphviz import Digraph

from ..core import (
    AsilBlock,
    Base,
    BasicEvent,
    CoverageBlock,
    PipelineBlock,
    SplitBlock,
    SumBlock,
)
from ..interfaces import FaultType, SafetyObserver
from .html_templates import get_coverage_label

# --- Type Definitions for better readability ---
PortMap: TypeAlias = dict[str, Optional[str]]
FlowMap: TypeAlias = dict[FaultType, PortMap]


class SafetyVisualizer(SafetyObserver):
    """Concrete observer that generates a Graphviz visualization of the safety architecture.

    It maps logical blocks to visual representations using Graphviz HTML-Labels
    and manages the auto-layouting of the signal flow.
    """

    # --- Layout Constants ---
    BLOCK_WIDTH_PIXEL = "72"
    BLOCK_HEIGHT_PIXEL = "72"
    BLOCK_WIDTH_DEZIMAL = "1.0"
    BLOCK_HEIGHT_DEZIMAL = "1.0"

    HEADER_HEIGHT = "32"
    DATA_HEIGHT = "40"

    # --- Style Constants ---
    COLOR_HEADER = "gray90"
    COLOR_BG = "white"
    COLOR_RF = "red"
    COLOR_LATENT = "blue"
    COLOR_TEXT_SECONDARY = "gray50"
    COLOR_COMP_BG = "gray96"
    COLOR_COMP_BORDER = "gray80"
    STYLE_DOTTED = "dotted"
    STYLE_DASHED = "dashed"

    FONT_SIZE_HEADER = "9"
    FONT_SIZE_DATA = "8"

    # --- Graphviz Attributes ---
    BASIC_EVENT_SHAPE = "circle"
    TRUE = "true"
    FALSE = "false"
    COMPASS_NORTH = "n"
    COMPASS_SOUTH = "s"

    # --- ID & Group Prefixes ---
    PREFIX_NODE_BE = "be_"
    PREFIX_NODE_SPLIT = "split_"
    PREFIX_NODE_COV = "cov_"
    PREFIX_NODE_TRANS = "trans_"
    PREFIX_NODE_ASIL = "asil_"
    PREFIX_CLUSTER_SUM = "cluster_sum_"
    PREFIX_CLUSTER_PIPE = "cluster_pipe_"
    PREFIX_CLUSTER_COMP = "cluster_comp_"
    PREFIX_LANE = "lane_"
    RANK_SAME = "same"

    # --- Summation Node Constants ---
    PREFIX_NODE_SUM = "sum_"
    SUM_NODE_SHAPE = "circle"
    SUM_NODE_SIZE = "0.3"
    SUM_FONT_SIZE = "10"
    LABEL_PLUS = "+"

    # --- Key Constants ---
    PATH_TYPE_RF = "rf"
    PATH_TYPE_LATENT = "latent"

    def __init__(self, name: str):
        """Initializes the visualizer with a Graphviz Digraph.

        Args:
            name (str): The name of the resulting diagram (and output filename).
        """
        self.dot = Digraph(name=name)
        self.dot.attr(
            rankdir="BT",
            nodesep="1.0",
            ranksep="0.8",
            splines="spline",  # line, spline, polyline, ortho, curved,  try this compound ??
            newrank=self.TRUE,
        )
        self.dot.attr(
            "node",
            fixedsize=self.TRUE,
            width=self.BLOCK_WIDTH_DEZIMAL,
            height=self.BLOCK_HEIGHT_DEZIMAL,
        )
        self.dot.attr("edge", arrowhead="none")

    # --- Helper Methods ---

    def _get_node_id(self, prefix: str, block: Any) -> str:
        """Generates a consistent and unique identifier for a Graphviz node.

        The ID is constructed using a block-specific prefix, the fault or block name,
        and the unique object memory address to prevent collisions.

        Args:
            prefix (str): The type-specific prefix (e.g., PREFIX_NODE_BE).
            block (Any): The block instance for which the ID is generated.

        Returns:
            str: A unique string identifier for the node.
        """
        base_name = (
            getattr(block, "name", None)
            or getattr(
                block,
                "fault_type",
                getattr(block, "target_fault", getattr(block, "fault_to_split", None)),
            ).name
        )
        return f"{prefix}{base_name}_{id(block)}"

    def _get_lane_id(self, fault_name: str, path_type: str) -> str:
        """Generates a consistent group identifier for vertical alignment (Lanes).

        Nodes sharing the same group ID are forced into the same vertical column by Graphviz.

        Args:
            fault_name (str): The name of the fault type (e.g., "SBE").
            path_type (str): The category of the path (rf or latent).

        Returns:
            str: A string identifier used for the 'group' attribute in Graphviz nodes.
        """
        return f"{self.PREFIX_LANE}{fault_name}_{path_type}"

    def _draw_junction(
        self,
        container: Digraph,
        fault: FaultType,
        branch_ports: list[str],
        original_port: Optional[str],
        color: str,
        path_type: str,
        block_id: int,
    ) -> Optional[str]:
        """Helper method to manage the convergence of multiple fault paths.

        If more than one path exists (e.g., from multiple parallel sub-blocks),
        it creates a '+' summation node. If only one path exists, it returns that
        path directly to avoid unnecessary visual clutter.

        Args:
            container (Digraph): The Graphviz container to draw in.
            fault (FaultType): The fault type being processed.
            branch_ports (list[str]): outgoing port IDs from parallel sub-blocks.
            original_port (Optional[str]): Incoming port ID before summation.
            color (str): Node/Edge color.
            path_type (str): 'rf' or 'latent'.
            block_id (int): ID of the parent SumBlock.

        Returns:
            Optional[str]: The port ID of the junction output (or single path).
        """
        all_srcs = list(set([p for p in branch_ports if p]))

        if len(all_srcs) == 0 and original_port:
            all_srcs.append(original_port)

        if len(all_srcs) > 1:
            j_id = f"{self.PREFIX_NODE_SUM}{fault.name}_{path_type}_{block_id}"
            group_id = self._get_lane_id(fault.name, path_type)

            container.node(
                j_id,
                label=self.LABEL_PLUS,
                shape=self.SUM_NODE_SHAPE,
                width=self.SUM_NODE_SIZE,
                height=self.SUM_NODE_SIZE,
                fixedsize=self.TRUE,
                color=color,
                fontcolor=color,
                fontsize=self.SUM_FONT_SIZE,
                group=group_id,
            )

            for src in all_srcs:
                container.edge(src, f"{j_id}:{self.COMPASS_SOUTH}", color=color, minlen="2")

            return f"{j_id}:{self.COMPASS_NORTH}"

        elif len(all_srcs) == 1:
            return all_srcs[0]

        return None

    # --- Main Logic ---

    def on_block_computed(
        self,
        block: Any,
        input_ports: FlowMap,
        spfm_in: dict[FaultType, float],
        lfm_in: dict[FaultType, float],
        spfm_out: dict[FaultType, float],
        lfm_out: dict[FaultType, float],
        container: Optional[Digraph] = None,
        predecessors: Optional[list[str]] = None,
    ) -> FlowMap:
        """Main entry point for the observer.

        Triggered after a hardware block completes its FIT rate transformation.
        Delegates the drawing task to specific internal visualization methods.

        Args:
            block (Any): The instance of the logic block being processed.
            input_ports (FlowMap): Mapping of fault types to incoming node IDs.
            spfm_in (dict[FaultType, float]): Incoming residual FIT rates.
            lfm_in (dict[FaultType, float]): Incoming latent FIT rates.
            spfm_out (dict[FaultType, float]): Outgoing residual FIT rates.
            lfm_out (dict[FaultType, float]): Outgoing latent FIT rates.
            container (Optional[Digraph]): Current subgraph context.
            predecessors (Optional[list[str]]): List of upstream anchors for alignment.

        Returns:
            FlowMap: Newly created output ports for the next block.
        """
        if container is None:
            container = self.dot

        if isinstance(block, BasicEvent):
            return self._draw_basic_event(block, spfm_out, lfm_out, container, predecessors)
        elif isinstance(block, SplitBlock):
            return self._draw_split_block(block, input_ports, spfm_out, lfm_out, container)
        elif isinstance(block, CoverageBlock):
            return self._draw_coverage_block(block, input_ports, spfm_out, lfm_out, container)
        elif isinstance(block, AsilBlock):
            return self._draw_asil_block(block, input_ports, spfm_out, lfm_out, container)
        elif isinstance(block, PipelineBlock):
            return self._draw_pipeline_block(block, input_ports, spfm_in, lfm_in, container)
        elif isinstance(block, SumBlock):
            return self._draw_sum_block(
                block,
                input_ports,
                spfm_in,
                lfm_in,
                spfm_out,
                lfm_out,
                container,
                predecessors,
            )
        elif isinstance(block, Base):
            cluster_name = f"{self.PREFIX_CLUSTER_COMP}{id(block)}"
            with container.subgraph(name=cluster_name) as c:
                full_label = f"{block.__class__.__name__}: {block.name}"
                c.attr(
                    label=full_label,
                    style="filled",
                    color=self.COLOR_COMP_BORDER,
                    bgcolor=self.COLOR_COMP_BG,
                )

                internal_inputs: FlowMap = {}
                local_anchors = []

                with c.subgraph() as in_rank:
                    in_rank.attr(rank="same")

                    for fault, paths in input_ports.items():
                        internal_inputs[fault] = {
                            self.PATH_TYPE_RF: None,
                            self.PATH_TYPE_LATENT: None,
                        }

                        if paths.get(self.PATH_TYPE_RF):
                            in_id = f"in_{id(block)}_{fault.name}_rf"
                            val = spfm_in.get(fault, 0.0)
                            label_text = f"In {fault.name}\n{val:.2f}"

                            in_rank.node(
                                in_id,
                                label=label_text,
                                shape="rect",
                                height="0.2",
                                style="filled",
                                fillcolor="white",
                                fontsize="7",
                                fixedsize="false",
                                group=self._get_lane_id(fault.name, self.PATH_TYPE_RF),
                            )
                            container.edge(
                                paths[self.PATH_TYPE_RF],
                                f"{in_id}:{self.COMPASS_SOUTH}",
                                color=self.COLOR_RF,
                            )
                            internal_inputs[fault][self.PATH_TYPE_RF] = f"{in_id}:{self.COMPASS_NORTH}"
                            local_anchors.append(f"{in_id}:{self.COMPASS_NORTH}")

                        if paths.get(self.PATH_TYPE_LATENT):
                            in_id_lat = f"in_{id(block)}_{fault.name}_lat"
                            val = lfm_in.get(fault, 0.0)
                            label_text = f"In {fault.name}\n{val:.2f}"

                            in_rank.node(
                                in_id_lat,
                                label=label_text,
                                shape="rect",
                                height="0.2",
                                style="filled",
                                fillcolor="white",
                                fontsize="7",
                                fixedsize="false",
                                group=self._get_lane_id(fault.name, self.PATH_TYPE_LATENT),
                            )
                            container.edge(
                                paths[self.PATH_TYPE_LATENT],
                                f"{in_id_lat}:{self.COMPASS_SOUTH}",
                                color=self.COLOR_LATENT,
                            )
                            internal_inputs[fault][self.PATH_TYPE_LATENT] = f"{in_id_lat}:{self.COMPASS_NORTH}"
                            local_anchors.append(f"{in_id_lat}:{self.COMPASS_NORTH}")

                active_inputs = internal_inputs if internal_inputs else input_ports
                active_predecessors = local_anchors if local_anchors else predecessors

                internal_results = self.on_block_computed(
                    block.root_block,
                    active_inputs,
                    spfm_in,
                    lfm_in,
                    spfm_out,
                    lfm_out,
                    container=c,
                    predecessors=active_predecessors,
                )

                final_outputs: FlowMap = {}
                with c.subgraph() as out_rank:
                    out_rank.attr(rank="same")

                    for fault, paths in internal_results.items():
                        final_outputs[fault] = {
                            self.PATH_TYPE_RF: None,
                            self.PATH_TYPE_LATENT: None,
                        }

                        if paths.get(self.PATH_TYPE_RF):
                            out_id = f"out_{id(block)}_{fault.name}_rf"
                            val = spfm_out.get(fault, 0.0)
                            label_text = f"Out {fault.name}\n{val:.2f}"

                            out_rank.node(
                                out_id,
                                label=label_text,
                                shape="rect",
                                height="0.2",
                                style="filled",
                                fillcolor="white",
                                fontsize="7",
                                fixedsize="false",
                                group=self._get_lane_id(fault.name, self.PATH_TYPE_RF),
                            )
                            c.edge(
                                paths[self.PATH_TYPE_RF],
                                f"{out_id}:{self.COMPASS_SOUTH}",
                                color=self.COLOR_RF,
                            )
                            final_outputs[fault][self.PATH_TYPE_RF] = f"{out_id}:{self.COMPASS_NORTH}"

                        if paths.get(self.PATH_TYPE_LATENT):
                            out_id_lat = f"out_{id(block)}_{fault.name}_lat"
                            val = lfm_out.get(fault, 0.0)
                            label_text = f"Out {fault.name}\n{val:.2f}"

                            out_rank.node(
                                out_id_lat,
                                label=label_text,
                                shape="rect",
                                height="0.2",
                                style="filled",
                                fillcolor="white",
                                fontsize="7",
                                fixedsize="false",
                                group=self._get_lane_id(fault.name, self.PATH_TYPE_LATENT),
                            )
                            c.edge(
                                paths[self.PATH_TYPE_LATENT],
                                f"{out_id_lat}:{self.COMPASS_SOUTH}",
                                color=self.COLOR_LATENT,
                            )
                            final_outputs[fault][self.PATH_TYPE_LATENT] = f"{out_id_lat}:{self.COMPASS_NORTH}"

                return final_outputs

        return input_ports

    def _draw_basic_event(
        self,
        block: BasicEvent,
        spfm_out: dict,
        lfm_out: dict,
        container: Digraph,
        predecessors: Optional[list[str]] = None,
    ) -> FlowMap:
        """Draws a circle for a FIT source (Basic Event)."""
        node_id = self._get_node_id(self.PREFIX_NODE_BE, block)
        label = f"{block.fault_type.name}\n{block.lambda_BE:.2f}"

        path_type = self.PATH_TYPE_RF if block.is_spfm else self.PATH_TYPE_LATENT
        group_id = self._get_lane_id(block.fault_type.name, path_type)
        color = self.COLOR_RF if block.is_spfm else self.COLOR_LATENT

        container.node(
            node_id,
            label=label,
            shape=self.BASIC_EVENT_SHAPE,
            width=self.BLOCK_WIDTH_DEZIMAL,
            height=self.BLOCK_HEIGHT_DEZIMAL,
            fixedsize=self.TRUE,
            color=color,
            fontcolor=color,
            group=group_id,
            fontsize=self.FONT_SIZE_HEADER,
        )

        if predecessors:
            container.edge(predecessors[0], f"{node_id}:{self.COMPASS_SOUTH}", style="invis")

        port_n = f"{node_id}:{self.COMPASS_NORTH}"

        return {
            block.fault_type: {
                self.PATH_TYPE_RF: port_n if block.is_spfm else None,
                self.PATH_TYPE_LATENT: port_n if not block.is_spfm else None,
            }
        }

    def _draw_split_block(
        self,
        block: SplitBlock,
        input_ports: FlowMap,
        spfm_out: dict,
        lfm_out: dict,
        container: Digraph,
    ) -> FlowMap:
        """Draws a SplitBlock as a fixed-size HTML table."""
        node_id = self._get_node_id(self.PREFIX_NODE_SPLIT, block)

        num_targets = len(block.distribution_rates)
        width_total = int(self.BLOCK_WIDTH_PIXEL)
        cell_width = width_total // num_targets

        cells = [
            f'<TD PORT="p_{tf.name}" WIDTH="{cell_width}" HEIGHT="{self.DATA_HEIGHT}" BGCOLOR="{self.COLOR_BG}"><FONT POINT-SIZE="{self.FONT_SIZE_DATA}">{p * 100:.1f}%</FONT></TD>'
            for tf, p in block.distribution_rates.items()
        ]

        label = (
            f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" WIDTH="{width_total}" '
            f'HEIGHT="{self.BLOCK_HEIGHT_PIXEL}" FIXEDSIZE="TRUE">'
            f"<TR>{''.join(cells)}</TR>"
            f"<TR>"
            f'<TD COLSPAN="{num_targets}" WIDTH="{width_total}" HEIGHT="{self.HEADER_HEIGHT}" '
            f'BGCOLOR="{self.COLOR_HEADER}"><B> Split {block.fault_to_split.name}</B></TD>'
            f"</TR></TABLE>>"
        )

        path_type = self.PATH_TYPE_RF if block.is_spfm else self.PATH_TYPE_LATENT
        group_id = self._get_lane_id(block.fault_to_split.name, path_type)

        container.node(node_id, label=label, shape="none", group=group_id)

        prev_ports = input_ports.get(block.fault_to_split, {})
        source_port = prev_ports.get(path_type)
        edge_color = self.COLOR_RF if block.is_spfm else self.COLOR_LATENT

        if source_port:
            container.edge(
                source_port,
                f"{node_id}:{self.COMPASS_SOUTH}",
                color=edge_color,
                minlen="2",
            )

        new_ports = input_ports.copy()
        for target_fault in block.distribution_rates.keys():
            port_ref = f"{node_id}:p_{target_fault.name}:{self.COMPASS_NORTH}"

            prev_target_ports = input_ports.get(target_fault, {self.PATH_TYPE_RF: None, self.PATH_TYPE_LATENT: None})

            if block.is_spfm:
                new_ports[target_fault] = {
                    self.PATH_TYPE_RF: port_ref,
                    self.PATH_TYPE_LATENT: prev_target_ports[self.PATH_TYPE_LATENT],
                }
            else:
                new_ports[target_fault] = {
                    self.PATH_TYPE_RF: prev_target_ports[self.PATH_TYPE_RF],
                    self.PATH_TYPE_LATENT: port_ref,
                }

        return new_ports

    def _draw_coverage_block(
        self,
        block: CoverageBlock,
        input_ports: FlowMap,
        spfm_out: dict,
        lfm_out: dict,
        container: Digraph,
    ) -> FlowMap:
        """Draws a CoverageBlock as a fixed-size HTML table."""
        node_id = self._get_node_id(self.PREFIX_NODE_COV, block)

        label = get_coverage_label(block.c_R, block.c_L)

        path_type = self.PATH_TYPE_RF if block.is_spfm else self.PATH_TYPE_LATENT
        group_id = self._get_lane_id(block.target_fault.name, path_type)

        container.node(node_id, label=label, shape="none", group=group_id)

        prev_ports = input_ports.get(block.target_fault, {})
        source_port = prev_ports.get(path_type)
        edge_color = self.COLOR_RF if block.is_spfm else self.COLOR_LATENT

        if source_port:
            container.edge(
                source_port,
                f"{node_id}:{self.COMPASS_SOUTH}",
                color=edge_color,
                minlen="2",
            )

        new_ports = input_ports.copy()
        port_rf = f"{node_id}:rf:{self.COMPASS_NORTH}"
        port_lat = f"{node_id}:latent:{self.COMPASS_NORTH}"

        if block.is_spfm:
            new_ports[block.target_fault] = {
                self.PATH_TYPE_RF: port_rf,
                self.PATH_TYPE_LATENT: port_lat,
            }
        else:
            new_ports[block.target_fault] = {
                self.PATH_TYPE_RF: prev_ports.get(self.PATH_TYPE_RF),
                self.PATH_TYPE_LATENT: port_lat,
            }

        return new_ports

    def _draw_asil_block(
        self,
        block: AsilBlock,
        input_ports: FlowMap,
        spfm_out: dict,
        lfm_out: dict,
        container: Digraph,
    ) -> FlowMap:
        """Draws the final ASIL evaluation block at the end of the chain."""
        node_id = self._get_node_id(self.PREFIX_NODE_ASIL, block)

        all_rf_srcs = []
        all_lat_srcs = []
        for ports in input_ports.values():
            if ports.get(self.PATH_TYPE_RF):
                all_rf_srcs.append(ports[self.PATH_TYPE_RF])
            if ports.get(self.PATH_TYPE_LATENT):
                all_lat_srcs.append(ports[self.PATH_TYPE_LATENT])

        cluster_name = f"cluster_final_{id(block)}"
        with container.subgraph(name=cluster_name) as c:
            c.attr(
                label="Final ASIL Evaluation",
                style=self.STYLE_DASHED,
                color=self.COLOR_HEADER,
                fontcolor=self.COLOR_TEXT_SECONDARY,
            )

            final_rf_sum = self._draw_junction(
                c,
                type("Final", (), {"name": "TOTAL"})(),
                all_rf_srcs,
                None,
                self.COLOR_RF,
                self.PATH_TYPE_RF,
                id(block),
            )

            final_lat_sum = self._draw_junction(
                c,
                type("Final", (), {"name": "TOTAL"})(),
                all_lat_srcs,
                None,
                self.COLOR_LATENT,
                self.PATH_TYPE_LATENT,
                id(block),
            )

            with c.subgraph() as s:
                s.attr(rank="sink")
                s.node(
                    node_id,
                    label="Calculate\nASIL Metrics",
                    shape="rectangle",
                    width=self.BLOCK_WIDTH_DEZIMAL,
                    height=self.BLOCK_HEIGHT_DEZIMAL,
                    style="filled",
                    fillcolor=self.COLOR_BG,
                    penwidth="2",
                )

            if final_rf_sum:
                container.edge(
                    final_rf_sum,
                    f"{node_id}:{self.COMPASS_SOUTH}",
                    color=self.COLOR_RF,
                    penwidth="2",
                )
            if final_lat_sum:
                container.edge(
                    final_lat_sum,
                    f"{node_id}:{self.COMPASS_SOUTH}",
                    color=self.COLOR_LATENT,
                    penwidth="2",
                )

        return {}

    def _draw_pipeline_block(
        self,
        block: PipelineBlock,
        input_ports: FlowMap,
        spfm_in: dict,
        lfm_in: dict,
        container: Digraph,
    ) -> FlowMap:
        """Orchestrates the visualization of a sequential chain of blocks."""
        current_ports = input_ports
        current_spfm = spfm_in
        current_lfm = lfm_in

        cluster_name = f"{self.PREFIX_CLUSTER_PIPE}{id(block)}"
        with container.subgraph(name=cluster_name) as c:
            c.attr(
                label=block.name,
                style=self.STYLE_DASHED,
                color=self.COLOR_HEADER,
                fontcolor=self.COLOR_TEXT_SECONDARY,
            )

            for sub_block in block.sub_blocks:
                anchors = []
                for p_dict in current_ports.values():
                    if p_dict.get(self.PATH_TYPE_RF):
                        anchors.append(p_dict[self.PATH_TYPE_RF])
                    if p_dict.get(self.PATH_TYPE_LATENT):
                        anchors.append(p_dict[self.PATH_TYPE_LATENT])

                next_spfm, next_lfm = sub_block.compute_fit(current_spfm, current_lfm)

                current_ports = self.on_block_computed(
                    sub_block,
                    current_ports,
                    current_spfm,
                    current_lfm,
                    next_spfm,
                    next_lfm,
                    container=c,
                    predecessors=anchors,
                )

                current_spfm, current_lfm = next_spfm, next_lfm

        return current_ports

    def _draw_sum_block(
        self,
        block: SumBlock,
        input_ports: FlowMap,
        spfm_in: dict,
        lfm_in: dict,
        spfm_out: dict,
        lfm_out: dict,
        container: Digraph,
        predecessors: Optional[list[str]] = None,
    ) -> FlowMap:
        """Draws a parallel aggregation block with summation nodes."""
        rf_collect = {}
        lat_collect = {}
        processed_rf = set()
        processed_lat = set()

        cluster_name = f"{self.PREFIX_CLUSTER_SUM}{id(block)}"
        with container.subgraph(name=cluster_name) as c:
            c.attr(
                label=block.name,
                style=self.STYLE_DOTTED,
                color=self.COLOR_HEADER,
                fontcolor=self.COLOR_TEXT_SECONDARY,
            )

            with c.subgraph() as logic_rank:
                for sub_block in block.sub_blocks:
                    child_spfm, child_lfm = sub_block.compute_fit(spfm_in, lfm_in)

                    child_res = self.on_block_computed(
                        sub_block,
                        input_ports,
                        spfm_in,
                        lfm_in,
                        child_spfm,
                        child_lfm,
                        logic_rank,
                        predecessors=predecessors,
                    )

                    is_processing_block = isinstance(
                        sub_block,
                        (
                            CoverageBlock,
                            SplitBlock,
                            PipelineBlock,
                        ),
                    )

                    for fault, ports in child_res.items():
                        original_rf = input_ports.get(fault, {}).get(self.PATH_TYPE_RF)
                        original_lat = input_ports.get(fault, {}).get(self.PATH_TYPE_LATENT)

                        is_source_block = isinstance(sub_block, BasicEvent) and sub_block.fault_type == fault

                        if ports.get(self.PATH_TYPE_RF):
                            has_changed = ports[self.PATH_TYPE_RF] != original_rf
                            if (is_source_block and sub_block.is_spfm) or has_changed:
                                rf_collect.setdefault(fault, []).append(ports[self.PATH_TYPE_RF])
                                if is_processing_block and has_changed:
                                    processed_rf.add(fault)

                        if ports.get(self.PATH_TYPE_LATENT):
                            has_changed = ports[self.PATH_TYPE_LATENT] != original_lat
                            if (is_source_block and not sub_block.is_spfm) or has_changed:
                                lat_collect.setdefault(fault, []).append(ports[self.PATH_TYPE_LATENT])
                                if is_processing_block and has_changed:
                                    processed_lat.add(fault)

            final_ports: FlowMap = {}
            all_faults = set(input_ports.keys()) | set(rf_collect.keys()) | set(lat_collect.keys())

            for fault in all_faults:
                final_ports[fault] = {
                    self.PATH_TYPE_RF: None,
                    self.PATH_TYPE_LATENT: None,
                }

                sources_rf = rf_collect.get(fault, [])
                orig_rf = input_ports.get(fault, {}).get(self.PATH_TYPE_RF)
                if fault not in processed_rf and orig_rf:
                    if orig_rf not in sources_rf:
                        sources_rf.append(orig_rf)

                final_ports[fault][self.PATH_TYPE_RF] = self._draw_junction(
                    c,
                    fault,
                    sources_rf,
                    None,
                    self.COLOR_RF,
                    self.PATH_TYPE_RF,
                    id(block),
                )

                sources_lat = lat_collect.get(fault, [])
                orig_lat = input_ports.get(fault, {}).get(self.PATH_TYPE_LATENT)
                if fault not in processed_lat and orig_lat:
                    if orig_lat not in sources_lat:
                        sources_lat.append(orig_lat)

                final_ports[fault][self.PATH_TYPE_LATENT] = self._draw_junction(
                    c,
                    fault,
                    sources_lat,
                    None,
                    self.COLOR_LATENT,
                    self.PATH_TYPE_LATENT,
                    id(block),
                )

        return final_ports

    def render(self, filename: str):
        """Exports the current graph to a PDF file.

        Args:
            filename (str): The path/name for the exported file (without extension).
        """
        self.dot.render(filename, view=True)
