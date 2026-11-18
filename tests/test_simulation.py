"""
tests/test_simulation.py — Phase 8 Simulation Lab tests
"""

import pytest
import networkx as nx

from src.backend.simulation import SimulationLab, SimulationReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_graph() -> nx.DiGraph:
    """
    Small deterministic graph:
        assumption_A  ──►  claim_B  ──►  conclusion_C
                                    └──►  conclusion_D
    All nodes start with confidence_score = 1.0.
    """
    G = nx.DiGraph()
    G.add_node("A", label="Assumption A", node_type="assumption", confidence_score=1.0)
    G.add_node("B", label="Claim B",      node_type="claim",      confidence_score=1.0)
    G.add_node("C", label="Conclusion C", node_type="conclusion",  confidence_score=1.0)
    G.add_node("D", label="Conclusion D", node_type="conclusion",  confidence_score=1.0)
    G.add_edge("A", "B", weight=1.0)
    G.add_edge("B", "C", weight=1.0)
    G.add_edge("B", "D", weight=1.0)
    return G


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_simulation_report_has_warning():
    """Every simulation report must carry the NOT ESTABLISHED FACT warning."""
    lab = SimulationLab(_build_graph())
    report = lab.run_scenario(toggled_node_ids=["A"], scenario_label="Toggle A")
    assert "SIMULATION" in report.simulation_warning
    assert "NOT ESTABLISHED FACT" in report.simulation_warning


def test_toggled_node_confidence_does_not_mutate_live_graph():
    """The live graph must NOT be mutated by a simulation run."""
    G = _build_graph()
    lab = SimulationLab(G)
    lab.run_scenario(toggled_node_ids=["A"])
    assert G.nodes["A"]["confidence_score"] == 1.0, (
        "Live graph was mutated — simulation must only touch its deep-copy clone."
    )


def test_toggled_node_marked_in_report():
    """The delta for the toggled node must have is_toggled_assumption=True."""
    lab = SimulationLab(_build_graph())
    report = lab.run_scenario(toggled_node_ids=["A"])
    toggled = [d for d in report.deltas if d.node_id == "A"]
    assert len(toggled) == 1
    assert toggled[0].is_toggled_assumption is True


def test_non_toggled_nodes_not_marked():
    """Nodes that were NOT toggled must have is_toggled_assumption=False."""
    lab = SimulationLab(_build_graph())
    report = lab.run_scenario(toggled_node_ids=["A"])
    for d in report.deltas:
        if d.node_id != "A":
            assert d.is_toggled_assumption is False


def test_toggling_root_reduces_total_impact():
    """
    Setting the root assumption to confidence=0 should reduce (or at least not
    increase) the total weighted impact across the graph.
    """
    lab = SimulationLab(_build_graph())
    report = lab.run_scenario(toggled_node_ids=["A"])
    # Total impact should decrease when a root node's confidence is zeroed
    assert report.simulated_total_impact <= report.baseline_total_impact


def test_impact_change_pct_sign():
    """impact_change_pct must be negative when total impact decreases."""
    lab = SimulationLab(_build_graph())
    report = lab.run_scenario(toggled_node_ids=["A"])
    if report.simulated_total_impact < report.baseline_total_impact:
        assert report.impact_change_pct < 0


def test_to_dict_structure():
    """to_dict() must include all required keys."""
    lab = SimulationLab(_build_graph())
    report = lab.run_scenario(toggled_node_ids=["B"], scenario_label="Toggle B")
    d = report.to_dict()
    for key in ("scenario_label", "toggled_node_ids", "simulation_warning",
                 "baseline_total_impact", "simulated_total_impact",
                 "impact_change_pct", "deltas"):
        assert key in d, f"Missing key in report dict: {key}"
    assert d["scenario_label"] == "Toggle B"
    assert "B" in d["toggled_node_ids"]


def test_list_nodes_returns_all():
    """list_nodes() must return all 4 nodes from the test graph."""
    lab = SimulationLab(_build_graph())
    nodes = lab.list_nodes()
    ids = {n["node_id"] for n in nodes}
    assert ids == {"A", "B", "C", "D"}


def test_empty_graph_does_not_crash():
    """Simulation on an empty graph must return a valid report without crashing."""
    lab = SimulationLab(nx.DiGraph())
    report = lab.run_scenario(toggled_node_ids=[])
    assert isinstance(report, SimulationReport)
    assert report.baseline_total_impact == 0.0
    assert report.simulated_total_impact == 0.0
