"""
simulation.py — What-If Sandbox for MindVault

Clones the live epistemic knowledge graph into an isolated in-memory branch,
lets the caller toggle assumption truth-values (confidence_score → 0.0),
re-runs the impact cascade on the clone, and returns a side-by-side delta
report.  Results are always labelled SIMULATION — NOT ESTABLISHED FACT.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

import networkx as nx


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NodeDelta:
    """Change in a single node's computed impact score between baseline and simulation."""
    node_id: str
    label: str
    baseline_impact: float
    simulated_impact: float
    delta: float                      # simulated − baseline
    is_toggled_assumption: bool = False


@dataclass
class SimulationReport:
    """Full what-if report returned to the caller."""
    scenario_label: str
    toggled_node_ids: list[str]
    deltas: list[NodeDelta]
    baseline_total_impact: float
    simulated_total_impact: float
    impact_change_pct: float          # % change in total impact across graph
    simulation_warning: str = (
        "SIMULATION — NOT ESTABLISHED FACT. "
        "Results are based on a hypothetical counterfactual scenario."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_label": self.scenario_label,
            "toggled_node_ids": self.toggled_node_ids,
            "simulation_warning": self.simulation_warning,
            "baseline_total_impact": round(self.baseline_total_impact, 4),
            "simulated_total_impact": round(self.simulated_total_impact, 4),
            "impact_change_pct": round(self.impact_change_pct, 2),
            "deltas": [
                {
                    "node_id": d.node_id,
                    "label": d.label,
                    "baseline_impact": round(d.baseline_impact, 4),
                    "simulated_impact": round(d.simulated_impact, 4),
                    "delta": round(d.delta, 4),
                    "is_toggled_assumption": d.is_toggled_assumption,
                }
                for d in sorted(self.deltas, key=lambda x: abs(x.delta), reverse=True)
            ],
        }


# ---------------------------------------------------------------------------
# Impact scoring (mirrors graph.py logic — no circular import)
# ---------------------------------------------------------------------------

def _in_degree_impact(G: nx.DiGraph) -> dict[str, float]:
    """
    Simple impact score: normalised in-degree centrality weighted by
    node confidence_score.  Mirrors the offline fallback in graph.py.
    """
    n = G.number_of_nodes()
    if n == 0:
        return {}
    max_in = max((G.in_degree(v) for v in G.nodes()), default=1) or 1
    scores: dict[str, float] = {}
    for node_id in G.nodes():
        conf = G.nodes[node_id].get("confidence_score", 1.0)
        in_deg = G.in_degree(node_id)
        scores[node_id] = (in_deg / max_in) * conf
    return scores


def _pagerank_impact(G: nx.DiGraph) -> dict[str, float]:
    """PageRank-based impact, weighted by confidence_score."""
    if G.number_of_nodes() == 0:
        return {}
    try:
        import scipy  # noqa: F401
        pr = nx.pagerank(G, weight="weight")
    except (ImportError, ModuleNotFoundError):
        pr = nx.pagerank(G, weight=None)  # pure-Python fallback

    scores: dict[str, float] = {}
    for node_id, rank in pr.items():
        conf = G.nodes[node_id].get("confidence_score", 1.0)
        scores[node_id] = rank * conf
    return scores


def _compute_impact(G: nx.DiGraph) -> dict[str, float]:
    try:
        return _pagerank_impact(G)
    except Exception:
        return _in_degree_impact(G)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class SimulationLab:
    """
    What-If sandbox for the MindVault epistemic knowledge graph.

    Usage::

        lab = SimulationLab(live_graph)          # pass a networkx DiGraph
        report = lab.run_scenario(
            toggled_node_ids=["node-123"],
            scenario_label="What if assumption A is false?"
        )
        print(report.to_dict())
    """

    def __init__(self, live_graph: nx.DiGraph) -> None:
        self._live_graph = live_graph

    # ------------------------------------------------------------------
    # Core simulation
    # ------------------------------------------------------------------

    def run_scenario(
        self,
        toggled_node_ids: list[str],
        scenario_label: str = "Unnamed scenario",
    ) -> SimulationReport:
        """
        Toggle the confidence_score of each node in *toggled_node_ids* to 0.0
        (simulating "this assumption is false"), re-compute impact scores on a
        deep copy of the graph, and return a delta report.
        """
        # --- Baseline scores on the live graph ---
        baseline_scores = _compute_impact(self._live_graph)

        # --- Clone graph and apply toggles ---
        sim_graph: nx.DiGraph = copy.deepcopy(self._live_graph)
        for node_id in toggled_node_ids:
            if node_id in sim_graph.nodes:
                sim_graph.nodes[node_id]["confidence_score"] = 0.0

        # --- Simulated scores ---
        sim_scores = _compute_impact(sim_graph)

        # --- Build delta report ---
        all_node_ids = set(baseline_scores) | set(sim_scores)
        deltas: list[NodeDelta] = []
        for nid in all_node_ids:
            baseline_val = baseline_scores.get(nid, 0.0)
            sim_val = sim_scores.get(nid, 0.0)
            label = self._live_graph.nodes[nid].get("label", nid) if nid in self._live_graph.nodes else nid
            deltas.append(NodeDelta(
                node_id=nid,
                label=label,
                baseline_impact=baseline_val,
                simulated_impact=sim_val,
                delta=sim_val - baseline_val,
                is_toggled_assumption=nid in toggled_node_ids,
            ))

        baseline_total = sum(baseline_scores.values())
        sim_total = sum(sim_scores.values())
        change_pct = (
            ((sim_total - baseline_total) / baseline_total * 100)
            if baseline_total > 0
            else 0.0
        )

        return SimulationReport(
            scenario_label=scenario_label,
            toggled_node_ids=toggled_node_ids,
            deltas=deltas,
            baseline_total_impact=baseline_total,
            simulated_total_impact=sim_total,
            impact_change_pct=change_pct,
        )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def list_nodes(self) -> list[dict[str, Any]]:
        """Return all nodes with their ids, labels, and current confidence scores."""
        return [
            {
                "node_id": nid,
                "label": data.get("label", nid),
                "confidence_score": data.get("confidence_score", 1.0),
                "node_type": data.get("node_type", "unknown"),
            }
            for nid, data in self._live_graph.nodes(data=True)
        ]
