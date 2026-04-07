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
from .constants import (
    BASIC_EVENT_SHAPE,
    BLOCK_HEIGHT_DEZIMAL,
    BLOCK_WIDTH_DEZIMAL,
    COLOR_BG,
    COLOR_COMP_BG,
    COLOR_COMP_BORDER,
    COLOR_HEADER,
    COLOR_LATENT,
    COLOR_RF,
    COLOR_TEXT_SECONDARY,
    COMPASS_NORTH,
    COMPASS_SOUTH,
    FONT_SIZE_HEADER,
    LABEL_PLUS,
    PATH_TYPE_LATENT,
    PATH_TYPE_RF,
    PREFIX_CLUSTER_COMP,
    PREFIX_CLUSTER_PIPE,
    PREFIX_CLUSTER_SUM,
    PREFIX_LANE,
    PREFIX_NODE_ASIL,
    PREFIX_NODE_BE,
    PREFIX_NODE_COV,
    PREFIX_NODE_SPLIT,
    PREFIX_NODE_SUM,
    STYLE_DASHED,
    STYLE_DOTTED,
    SUM_FONT_SIZE,
    SUM_NODE_SHAPE,
    SUM_NODE_SIZE,
    TRUE,
)
from .html_templates import get_coverage_label, get_split_label

# --- Type Definitions for better readability ---
PortMap: TypeAlias = dict[str, Optional[str]]
FlowMap: TypeAlias = dict[FaultType, PortMap]


class SafetyVisualizer(SafetyObserver):
    """Concrete observer that generates a Graphviz visualization of the safety architecture.

    It maps logical blocks to visual representations using Graphviz HTML-Labels
    and manages the auto-layouting of the signal flow.
    """

    def __init__(self, name: str, merge_latent: bool = False):
        """Initializes the visualizer with a Graphviz Digraph.

        Args:
            name (str): The name of the resulting diagram (and output filename).
        """
        self.total_lfm_out_val = 0
        self.merge_latent = merge_latent
        self.current_latent_port: Optional[str] = None
        self.dot = Digraph(name=name)
        self.dot.attr(
            rankdir="BT",
            nodesep="1.5",
            ranksep="1.2",
            splines="spline",  # line, spline, polyline, ortho, curved,  try this compound ??
            newrank=TRUE,
            # concentrate="true",
        )
        self.dot.attr(
            "node",
            fixedsize=TRUE,
            width=BLOCK_WIDTH_DEZIMAL,
            height=BLOCK_HEIGHT_DEZIMAL,
        )
        self.dot.attr("edge", arrowhead="none")

    # --- Helper Methods ---

    def _accumulate_latent_paths(self, container: Digraph, ports: FlowMap, block_id: int) -> FlowMap:
        """Führt alle latenten Pfade eines Blocks zu einem einzigen Bus-Port zusammen."""
        if not self.merge_latent:
            return ports

        # 1. Sammle alle neuen latenten Ports aus der aktuellen FlowMap
        new_latent_srcs = []
        for fault_ports in ports.values():
            port = fault_ports.get(PATH_TYPE_LATENT)
            if port and port != self.current_latent_port:
                new_latent_srcs.append(port)

        if not new_latent_srcs:
            return ports

        # 2. Wenn bereits ein Bus existiert, füge ihn zu den Quellen hinzu
        if self.current_latent_port:
            new_latent_srcs.append(self.current_latent_port)

        # 3. Erzeuge einen Junction-Knoten (+) für den Bus
        # Wir nutzen eine feste Lane für den globalen latenten Pfad (z.B. ganz rechts)
        bus_lane = self._get_lane_id("GLOBAL", PATH_TYPE_LATENT)

        j_id = f"latent_bus_{block_id}"
        container.node(j_id, label=LABEL_PLUS, shape=SUM_NODE_SHAPE, width=SUM_NODE_SIZE, height=SUM_NODE_SIZE, color=COLOR_LATENT, fontcolor=COLOR_LATENT, group=bus_lane)

        for src in new_latent_srcs:
            container.edge(src, f"{j_id}:{COMPASS_SOUTH}", color=COLOR_LATENT)

        self.current_latent_port = f"{j_id}:{COMPASS_NORTH}"

        updated_ports = ports.copy()
        for ft in updated_ports:
            updated_ports[ft] = updated_ports[ft].copy()
            updated_ports[ft][PATH_TYPE_LATENT] = self.current_latent_port

        return updated_ports

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
        return f"{PREFIX_LANE}{fault_name}_{path_type}"

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
            j_id = f"{PREFIX_NODE_SUM}{fault.name}_{path_type}_{block_id}"
            group_id = self._get_lane_id(fault.name, path_type)

            container.node(
                j_id,
                label=LABEL_PLUS,
                shape=SUM_NODE_SHAPE,
                width=SUM_NODE_SIZE,
                height=SUM_NODE_SIZE,
                fixedsize=TRUE,
                color=color,
                fontcolor=color,
                fontsize=SUM_FONT_SIZE,
                group=group_id,
            )

            for src in all_srcs:
                container.edge(
                    src,
                    f"{j_id}:{COMPASS_SOUTH}",
                    color=color,
                    minlen="2",
                    weight="10",  # <-- HIER HINZUFÜGEN
                )

            return f"{j_id}:{COMPASS_NORTH}"

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
            out_ports = input_ports.copy()
            out_ports.update(self._draw_basic_event(block, spfm_out, lfm_out, container, predecessors))
            return out_ports
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
            cluster_name = f"{PREFIX_CLUSTER_COMP}{id(block)}"
            with container.subgraph(name=cluster_name) as c:
                full_label = f"{block.__class__.__name__}: {block.name}"
                c.attr(
                    label=full_label,
                    style="filled",
                    color=COLOR_COMP_BORDER,
                    bgcolor=COLOR_COMP_BG,
                )

                internal_inputs: FlowMap = {}
                local_anchors = []

                with c.subgraph() as in_rank:
                    in_rank.attr(rank="same")

                    for fault, paths in input_ports.items():
                        internal_inputs[fault] = {
                            PATH_TYPE_RF: None,
                            PATH_TYPE_LATENT: None,
                        }

                        if paths.get(PATH_TYPE_RF):
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
                                group=self._get_lane_id(fault.name, PATH_TYPE_RF),
                            )
                            container.edge(paths[PATH_TYPE_RF], f"{in_id}:{COMPASS_SOUTH}", color=COLOR_RF, weight="10")
                            internal_inputs[fault][PATH_TYPE_RF] = f"{in_id}:{COMPASS_NORTH}"
                            local_anchors.append(f"{in_id}:{COMPASS_NORTH}")

                        if paths.get(PATH_TYPE_LATENT):
                            if self.merge_latent:
                                pass
                            else:
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
                                    group=self._get_lane_id(fault.name, PATH_TYPE_LATENT),
                                )
                                container.edge(paths[PATH_TYPE_LATENT], f"{in_id_lat}:{COMPASS_SOUTH}", color=COLOR_LATENT, weight="10")
                                internal_inputs[fault][PATH_TYPE_LATENT] = f"{in_id_lat}:{COMPASS_NORTH}"
                                local_anchors.append(f"{in_id_lat}:{COMPASS_NORTH}")

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

                # Vor der Schleife: Prüfen, ob WIRKLICH NEUE Latent-Pfade erzeugt wurden
                # (Ignoriere Pfade, die einfach nur der durchgeschleifte alte Bus sind)
                new_latent_paths = [paths[PATH_TYPE_LATENT] for paths in internal_results.values() if paths.get(PATH_TYPE_LATENT) and paths[PATH_TYPE_LATENT] != self.current_latent_port]
                has_new_latent = len(new_latent_paths) > 0

                final_outputs: FlowMap = {}

                with c.subgraph() as out_rank:
                    out_rank.attr(rank="same")

                    # 1. Den blauen Plus-Knoten auf der rechten Seite erstellen
                    # (ABER NUR, wenn dieser Block auch wirklich neue Latent-Fehler erzeugt)
                    if self.merge_latent and has_new_latent:
                        latent_junction_id = f"out_junction_{id(block)}_lat"
                        out_rank.node(
                            latent_junction_id,
                            label=LABEL_PLUS,
                            shape=SUM_NODE_SHAPE,
                            width=SUM_NODE_SIZE,
                            height=SUM_NODE_SIZE,
                            fixedsize="true",
                            color=COLOR_LATENT,
                            fontcolor=COLOR_LATENT,
                            fontsize=SUM_FONT_SIZE,
                            group=self._get_lane_id("GLOBAL", PATH_TYPE_LATENT),
                        )
                        # Der blaue Bus kommt von UNTEN (SOUTH) und geht nach OBEN (NORTH)
                        if self.current_latent_port:
                            c.edge(self.current_latent_port, f"{latent_junction_id}:{COMPASS_SOUTH}", color=COLOR_LATENT, weight="100")

                        # Alten Port merken, um Duplikate auszufiltern
                        old_latent_port = self.current_latent_port
                        self.current_latent_port = f"{latent_junction_id}:{COMPASS_NORTH}"
                    else:
                        old_latent_port = self.current_latent_port
                        latent_junction_id = None

                    # Set, um mehrfache Linien vom selben internen SumBlock zu verhindern
                    connected_latent_ports = set()

                    # 2. Die normalen Ausgänge generieren
                    for fault, paths in internal_results.items():
                        final_outputs[fault] = {
                            PATH_TYPE_RF: None,
                            PATH_TYPE_LATENT: None,
                        }

                        # -- Residual Fault (RF) Logik (unverändert) --
                        if paths.get(PATH_TYPE_RF):
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
                                group=self._get_lane_id(fault.name, PATH_TYPE_RF),
                            )
                            c.edge(paths[PATH_TYPE_RF], f"{out_id}:{COMPASS_SOUTH}", color=COLOR_RF, weight="10")
                            final_outputs[fault][PATH_TYPE_RF] = f"{out_id}:{COMPASS_NORTH}"

                        # -- Latent Fault Logik --
                        if paths.get(PATH_TYPE_LATENT):
                            if self.merge_latent:
                                port_to_connect = paths[PATH_TYPE_LATENT]
                                # Verbinde NUR, wenn es eine NEUE Quelle ist und wir diesen Port nicht schon verbunden haben
                                if port_to_connect != old_latent_port and latent_junction_id:
                                    if port_to_connect not in connected_latent_ports:
                                        c.edge(port_to_connect, latent_junction_id, color=COLOR_LATENT)
                                        connected_latent_ports.add(port_to_connect)
                            else:
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
                                    group=self._get_lane_id(fault.name, PATH_TYPE_LATENT),
                                )
                                c.edge(paths[PATH_TYPE_LATENT], f"{out_id_lat}:{COMPASS_SOUTH}", color=COLOR_LATENT, weight="10")
                                final_outputs[fault][PATH_TYPE_LATENT] = f"{out_id_lat}:{COMPASS_NORTH}"

                # 3. Jeden Fehler-Typ auf den aktuellen Bus referenzieren
                if self.merge_latent:
                    for fault in input_ports.keys() | internal_results.keys():
                        if fault not in final_outputs:
                            final_outputs[fault] = {PATH_TYPE_RF: None, PATH_TYPE_LATENT: None}
                        final_outputs[fault][PATH_TYPE_LATENT] = self.current_latent_port

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
        node_id = self._get_node_id(PREFIX_NODE_BE, block)
        label = f"{block.fault_type.name}\n{block.lambda_BE:.2f}"

        path_type = PATH_TYPE_RF if block.is_spfm else PATH_TYPE_LATENT
        group_id = self._get_lane_id(block.fault_type.name, path_type)
        color = COLOR_RF if block.is_spfm else COLOR_LATENT

        container.node(
            node_id,
            label=label,
            shape=BASIC_EVENT_SHAPE,
            width=BLOCK_WIDTH_DEZIMAL,
            height=BLOCK_HEIGHT_DEZIMAL,
            fixedsize=TRUE,
            color=color,
            fontcolor=color,
            group=group_id,
            fontsize=FONT_SIZE_HEADER,
        )

        if predecessors:
            container.edge(
                predecessors[0],
                f"{node_id}:{COMPASS_SOUTH}",
                style="invis",
                weight="10",  # <-- HIER HINZUFÜGEN
            )

        port_n = f"{node_id}:{COMPASS_NORTH}"

        return {
            block.fault_type: {
                PATH_TYPE_RF: port_n if block.is_spfm else None,
                PATH_TYPE_LATENT: port_n if not block.is_spfm else None,
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
        node_id = self._get_node_id(PREFIX_NODE_SPLIT, block)

        label = get_split_label(block)

        path_type = PATH_TYPE_RF if block.is_spfm else PATH_TYPE_LATENT
        group_id = self._get_lane_id(block.fault_to_split.name, path_type)

        container.node(node_id, label=label, shape="none", group=group_id)

        prev_ports = input_ports.get(block.fault_to_split, {})
        source_port = prev_ports.get(path_type)
        edge_color = COLOR_RF if block.is_spfm else COLOR_LATENT

        if source_port:
            container.edge(
                source_port,
                f"{node_id}:{COMPASS_SOUTH}",
                color=edge_color,
                minlen="2",
                weight="10",  # <-- HIER HINZUFÜGEN
            )

        new_ports = input_ports.copy()
        for target_fault in block.distribution_rates.keys():
            port_ref = f"{node_id}:p_{target_fault.name}:{COMPASS_NORTH}"

            prev_target_ports = input_ports.get(target_fault, {PATH_TYPE_RF: None, PATH_TYPE_LATENT: None})

            if block.is_spfm:
                new_ports[target_fault] = {
                    PATH_TYPE_RF: port_ref,
                    PATH_TYPE_LATENT: prev_target_ports[PATH_TYPE_LATENT],
                }
            else:
                new_ports[target_fault] = {
                    PATH_TYPE_RF: prev_target_ports[PATH_TYPE_RF],
                    PATH_TYPE_LATENT: port_ref,
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
        node_id = self._get_node_id(PREFIX_NODE_COV, block)

        label = get_coverage_label(block.c_R, block.c_L)

        path_type = PATH_TYPE_RF if block.is_spfm else PATH_TYPE_LATENT
        group_id = self._get_lane_id(block.target_fault.name, path_type)

        container.node(node_id, label=label, shape="none", group=group_id)

        prev_ports = input_ports.get(block.target_fault, {})
        source_port = prev_ports.get(path_type)
        edge_color = COLOR_RF if block.is_spfm else COLOR_LATENT

        if source_port:
            container.edge(
                source_port,
                f"{node_id}:{COMPASS_SOUTH}",
                color=edge_color,
                minlen="2",
                weight="10",  # <-- HIER HINZUFÜGEN
            )

        new_ports = input_ports.copy()
        port_rf = f"{node_id}:rf:{COMPASS_NORTH}"
        port_lat = f"{node_id}:latent:{COMPASS_NORTH}"

        if block.is_spfm:
            prev_lat = prev_ports.get(PATH_TYPE_LATENT)
            if prev_lat:
                # Verbindet den alten Latent-Pfad mit dem neu generierten vom CoverageBlock
                j_id = f"{PREFIX_NODE_SUM}{block.target_fault.name}_lat_{id(block)}"
                group_lat = self._get_lane_id(block.target_fault.name, PATH_TYPE_LATENT)

                container.node(
                    j_id,
                    label=LABEL_PLUS,
                    shape=SUM_NODE_SHAPE,
                    width=SUM_NODE_SIZE,
                    height=SUM_NODE_SIZE,
                    fixedsize=TRUE,
                    color=COLOR_LATENT,
                    fontcolor=COLOR_LATENT,
                    fontsize=SUM_FONT_SIZE,
                    group=group_lat,
                )

                container.edge(prev_lat, f"{j_id}:{COMPASS_SOUTH}", color=COLOR_LATENT, weight="10")
                container.edge(port_lat, f"{j_id}:{COMPASS_SOUTH}", color=COLOR_LATENT, weight="10")
                merged_lat = f"{j_id}:{COMPASS_NORTH}"
            else:
                merged_lat = port_lat

            new_ports[block.target_fault] = {
                PATH_TYPE_RF: port_rf,
                PATH_TYPE_LATENT: merged_lat,
            }
        else:
            new_ports[block.target_fault] = {
                PATH_TYPE_RF: prev_ports.get(PATH_TYPE_RF),
                PATH_TYPE_LATENT: port_lat,
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
        node_id = self._get_node_id(PREFIX_NODE_ASIL, block)

        all_rf_srcs = []
        all_lat_srcs = []
        for ports in input_ports.values():
            if ports.get(PATH_TYPE_RF):
                all_rf_srcs.append(ports[PATH_TYPE_RF])
            if ports.get(PATH_TYPE_LATENT):
                all_lat_srcs.append(ports[PATH_TYPE_LATENT])

        cluster_name = f"cluster_final_{id(block)}"
        with container.subgraph(name=cluster_name) as c:
            c.attr(
                label="Final ASIL Evaluation",
                style=STYLE_DASHED,
                color=COLOR_HEADER,
                fontcolor=COLOR_TEXT_SECONDARY,
            )

            final_rf_sum = self._draw_junction(
                c,
                type("Final", (), {"name": "TOTAL"})(),
                all_rf_srcs,
                None,
                COLOR_RF,
                PATH_TYPE_RF,
                id(block),
            )

            final_lat_sum = self._draw_junction(
                c,
                type("Final", (), {"name": "TOTAL"})(),
                all_lat_srcs,
                None,
                COLOR_LATENT,
                PATH_TYPE_LATENT,
                id(block),
            )

            with c.subgraph() as s:
                s.attr(rank="sink")
                s.node(
                    node_id,
                    label="Calculate\nASIL Metrics",
                    shape="rectangle",
                    width=BLOCK_WIDTH_DEZIMAL,
                    height=BLOCK_HEIGHT_DEZIMAL,
                    style="filled",
                    fillcolor=COLOR_BG,
                    penwidth="2",
                )

            if final_rf_sum:
                container.edge(
                    final_rf_sum,
                    f"{node_id}:{COMPASS_SOUTH}",
                    color=COLOR_RF,
                    penwidth="2",
                )
            if final_lat_sum:
                container.edge(
                    final_lat_sum,
                    f"{node_id}:{COMPASS_SOUTH}",
                    color=COLOR_LATENT,
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

        cluster_name = f"{PREFIX_CLUSTER_PIPE}{id(block)}"
        with container.subgraph(name=cluster_name) as c:
            c.attr(
                label=block.name,
                style=STYLE_DASHED,
                color=COLOR_HEADER,
                fontcolor=COLOR_TEXT_SECONDARY,
            )

            for sub_block in block.sub_blocks:
                anchors = []
                for p_dict in current_ports.values():
                    if p_dict.get(PATH_TYPE_RF):
                        anchors.append(p_dict[PATH_TYPE_RF])
                    if p_dict.get(PATH_TYPE_LATENT):
                        anchors.append(p_dict[PATH_TYPE_LATENT])

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

        # SICHERE DEN EINGANGS-BUS FÜR ALLE PARALLELEN BLÖCKE
        incoming_latent_port = self.current_latent_port
        outgoing_latent_ports = []

        cluster_name = f"{PREFIX_CLUSTER_SUM}{id(block)}"
        with container.subgraph(name=cluster_name) as c:
            c.attr(
                label=block.name,
                style=STYLE_DOTTED,
                color=COLOR_HEADER,
                fontcolor=COLOR_TEXT_SECONDARY,
            )

            with c.subgraph() as logic_rank:
                for sub_block in block.sub_blocks:
                    # VOR JEDEM PARALLELEN BLOCK: SETZE DEN BUS ZURÜCK AUF DEN EINGANG!
                    if self.merge_latent:
                        self.current_latent_port = incoming_latent_port

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

                    # NACH JEDEM PARALLELEN BLOCK: MERKE DIR DEN AUSGANGS-BUS DIESES PFADS
                    if self.merge_latent:
                        if self.current_latent_port and self.current_latent_port not in outgoing_latent_ports:
                            outgoing_latent_ports.append(self.current_latent_port)

                    is_processing_block = isinstance(
                        sub_block,
                        (CoverageBlock, SplitBlock, PipelineBlock),
                    )

                    for fault, ports in child_res.items():
                        original_rf = input_ports.get(fault, {}).get(PATH_TYPE_RF)
                        original_lat = input_ports.get(fault, {}).get(PATH_TYPE_LATENT)

                        is_source_block = isinstance(sub_block, BasicEvent) and sub_block.fault_type == fault

                        if ports.get(PATH_TYPE_RF):
                            has_changed = ports[PATH_TYPE_RF] != original_rf
                            if (is_source_block and sub_block.is_spfm) or has_changed:
                                rf_collect.setdefault(fault, []).append(ports[PATH_TYPE_RF])
                                if is_processing_block and has_changed:
                                    processed_rf.add(fault)

                        if ports.get(PATH_TYPE_LATENT):
                            has_changed = ports[PATH_TYPE_LATENT] != original_lat
                            if (is_source_block and not sub_block.is_spfm) or has_changed:
                                lat_collect.setdefault(fault, []).append(ports[PATH_TYPE_LATENT])
                                if is_processing_block and has_changed:
                                    processed_lat.add(fault)

            final_ports: FlowMap = {}
            all_faults = set(input_ports.keys()) | set(rf_collect.keys()) | set(lat_collect.keys())

            for fault in all_faults:
                final_ports[fault] = {
                    PATH_TYPE_RF: None,
                    PATH_TYPE_LATENT: None,
                }

                # --- RF Logik (unverändert) ---
                sources_rf = rf_collect.get(fault, [])
                orig_rf = input_ports.get(fault, {}).get(PATH_TYPE_RF)
                if fault not in processed_rf and orig_rf:
                    if orig_rf not in sources_rf:
                        sources_rf.append(orig_rf)

                final_ports[fault][PATH_TYPE_RF] = self._draw_junction(c, fault, sources_rf, None, COLOR_RF, PATH_TYPE_RF, id(block))

                # --- LATENT Logik (Trennung von lokalen und globalen Ports) ---
                sources_lat = lat_collect.get(fault, [])
                orig_lat = input_ports.get(fault, {}).get(PATH_TYPE_LATENT)
                if fault not in processed_lat and orig_lat:
                    if orig_lat not in sources_lat:
                        sources_lat.append(orig_lat)

                if self.merge_latent:
                    # Filtere den globalen Bus heraus, verbinde nur Coverage und Basic Events
                    local_sources_lat = [p for p in sources_lat if p and "out_junction_" not in p and "sum_bus_" not in p and "latent_bus_" not in p]

                    if local_sources_lat:
                        final_ports[fault][PATH_TYPE_LATENT] = self._draw_junction(c, fault, local_sources_lat, None, COLOR_LATENT, PATH_TYPE_LATENT, id(block))
                    else:
                        final_ports[fault][PATH_TYPE_LATENT] = None
                else:
                    final_ports[fault][PATH_TYPE_LATENT] = self._draw_junction(c, fault, sources_lat, None, COLOR_LATENT, PATH_TYPE_LATENT, id(block))

            # --- ZUSAMMENFÜHRUNG DER PARALLELEN BUSSE ---
            if self.merge_latent:
                valid_out_ports = [p for p in outgoing_latent_ports if p != incoming_latent_port]

                if len(valid_out_ports) > 1:
                    bus_junction_id = f"sum_bus_{id(block)}_lat"
                    c.node(
                        bus_junction_id,
                        label=LABEL_PLUS,
                        shape=SUM_NODE_SHAPE,
                        width=SUM_NODE_SIZE,
                        height=SUM_NODE_SIZE,
                        fixedsize="true",
                        color=COLOR_LATENT,
                        fontcolor=COLOR_LATENT,
                        fontsize=SUM_FONT_SIZE,
                        group=self._get_lane_id("GLOBAL", PATH_TYPE_LATENT),
                    )

                    if incoming_latent_port:
                        c.edge(incoming_latent_port, f"{bus_junction_id}:{COMPASS_SOUTH}", color=COLOR_LATENT, weight="100")
                    for port in valid_out_ports:
                        c.edge(port, f"{bus_junction_id}:{COMPASS_SOUTH}", color=COLOR_LATENT)

                    self.current_latent_port = f"{bus_junction_id}:{COMPASS_NORTH}"
                elif len(valid_out_ports) == 1:
                    self.current_latent_port = valid_out_ports[0]
                else:
                    self.current_latent_port = incoming_latent_port

                # Allen fehlenden Ports den aktuellen Bus zuweisen (verhindert das Verschlucken der globalen Ports)
                for fault in final_ports:
                    if not final_ports[fault][PATH_TYPE_LATENT]:
                        final_ports[fault][PATH_TYPE_LATENT] = self.current_latent_port

        return final_ports

    def render(self, filename: str):
        """Exports the current graph to a PDF file.

        Args:
            filename (str): The path/name for the exported file (without extension).
        """
        self.dot.render(filename, view=True)
