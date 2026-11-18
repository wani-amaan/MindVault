"""
MindVault Critical Thinking Engine
Deterministic heuristic scanner that flags reasoning errors, unsupported leaps,
circular dependencies, correlation-causation confusions, and logical gaps.
"""
import re
from typing import List, Dict, Any, Optional
from src.backend.models import KnowledgeNodeModel, ClaimModel, GraphEdgeModel
from src.backend.graph import KnowledgeGraphEngine


CAUSATION_CLAIM_PATTERNS = [
    r"\b(causes?|leads?\s+to|results?\s+in|produces?|triggers?)\b"
]
CORRELATION_SIGNALS = [
    r"\b(correlates?\s+with|associated\s+with|linked\s+to|related\s+to|co-occurs?\s+with)\b"
]
WEASEL_SIGNALS = [
    r"\b(everyone\s+knows|obviously|clearly|it\s+is\s+well.?known|undeniably|certainly|always|never)\b"
]
LOGICAL_LEAP_SIGNALS = [
    r"\b(therefore|thus|hence|so\s+it\s+follows|this\s+proves?)\b"
]


def _search_patterns(text: str, patterns: List[str]) -> bool:
    """Returns True if any pattern matches in the text."""
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


class ReasoningIssue:
    def __init__(self, issue_type: str, description: str, severity: str, node_id: Optional[str] = None):
        self.issue_type = issue_type
        self.description = description
        self.severity = severity  # 'HIGH', 'MEDIUM', 'LOW'
        self.node_id = node_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "description": self.description,
            "severity": self.severity,
            "node_id": self.node_id
        }


class CriticalThinkingEngine:
    def __init__(self, graph_engine: KnowledgeGraphEngine):
        self.graph = graph_engine

    def scan_node(self, node: KnowledgeNodeModel) -> List[ReasoningIssue]:
        """Runs a full heuristic scan on a single knowledge node."""
        issues = []
        text = f"{node.title} {node.content}"

        # Check 1: Correlation-Causation Confusion
        if _search_patterns(text, CAUSATION_CLAIM_PATTERNS) and _search_patterns(text, CORRELATION_SIGNALS):
            issues.append(ReasoningIssue(
                issue_type="CORRELATION_CAUSATION_CONFUSION",
                description=(
                    f"Node '{node.title}' uses both correlation language and causal claims simultaneously. "
                    "Correlation does not establish causation. Consider stating the relationship more precisely."
                ),
                severity="HIGH",
                node_id=node.id
            ))

        # Check 2: Unsupported Logical Leap
        if _search_patterns(text, LOGICAL_LEAP_SIGNALS):
            issues.append(ReasoningIssue(
                issue_type="UNSUPPORTED_LOGICAL_LEAP",
                description=(
                    f"Node '{node.title}' uses conclusion-signalling language "
                    "('therefore', 'thus', 'hence', etc.). Ensure the preceding premises "
                    "are explicitly stated and evidence-grounded."
                ),
                severity="MEDIUM",
                node_id=node.id
            ))

        # Check 3: Overgeneralisation via Weasel Words
        if _search_patterns(text, WEASEL_SIGNALS):
            issues.append(ReasoningIssue(
                issue_type="OVERGENERALISATION",
                description=(
                    f"Node '{node.title}' contains absolute or unverified generalisation signals "
                    "('always', 'never', 'everyone knows', 'obviously', etc.). "
                    "These assertions require specific evidential support."
                ),
                severity="MEDIUM",
                node_id=node.id
            ))

        return issues

    def detect_circular_dependencies(self) -> List[ReasoningIssue]:
        """
        Uses NetworkX cycle detection to identify circular epistemic reasoning chains.
        A circular dependency A → B → C → A means no independent grounding exists.
        """
        issues = []
        try:
            cycles = list(nx_simple_cycles(self.graph.graph))
            for cycle in cycles:
                cycle_labels = " → ".join(
                    self.graph.graph.nodes[n].get("title", n[:8]) for n in cycle
                ) + f" → {self.graph.graph.nodes[cycle[0]].get('title', cycle[0][:8])}"
                issues.append(ReasoningIssue(
                    issue_type="CIRCULAR_DEPENDENCY",
                    description=(
                        f"Circular epistemic chain detected: [{cycle_labels}]. "
                        "This creates an unfounded self-referential belief loop with no independent anchor."
                    ),
                    severity="HIGH",
                    node_id=cycle[0]
                ))
        except Exception:
            pass
        return issues

    def scan_all_nodes(self, nodes: List[KnowledgeNodeModel]) -> List[ReasoningIssue]:
        """Runs the full heuristic scan across all provided knowledge nodes."""
        all_issues = []
        for node in nodes:
            all_issues.extend(self.scan_node(node))
        all_issues.extend(self.detect_circular_dependencies())
        return all_issues


def nx_simple_cycles(graph):
    """Wrapper for networkx simple_cycles for testability."""
    import networkx as nx
    return list(nx.simple_cycles(graph))
