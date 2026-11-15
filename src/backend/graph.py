"""
MindVault Knowledge Graph & Impact Radar Engine
Constructs an in-memory directed epistemic graph via NetworkX and computes:
  - Foundation scoring (PageRank + in-degree centrality)
  - Epistemic vulnerability cascades (reverse-dependency traversal)
  - Graph serialization for frontend interactive visualization
"""
import json
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
import aiosqlite
from src.backend.database import DatabaseEngine
from src.backend.models import GraphEdgeModel, generate_uuid, utc_now


class KnowledgeGraphEngine:
    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine
        self.graph: nx.DiGraph = nx.DiGraph()

    async def build_from_db(self):
        """
        Loads all knowledge_nodes and graph_edges from SQLite
        and constructs the in-memory NetworkX directed graph.
        """
        self.graph.clear()

        async with aiosqlite.connect(self.db.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            # Load all nodes with metadata
            async with conn.execute("SELECT id, node_type, title, status, confidence_score FROM knowledge_nodes") as cursor:
                async for row in cursor:
                    self.graph.add_node(
                        row["id"],
                        node_type=row["node_type"],
                        title=row["title"],
                        status=row["status"],
                        confidence_score=row["confidence_score"]
                    )

            # Load all directed edges
            async with conn.execute("SELECT id, source_node_id, target_node_id, relation_type, weight FROM graph_edges") as cursor:
                async for row in cursor:
                    self.graph.add_edge(
                        row["source_node_id"],
                        row["target_node_id"],
                        edge_id=row["id"],
                        relation_type=row["relation_type"],
                        weight=row["weight"]
                    )

    async def add_edge(self, edge: GraphEdgeModel) -> GraphEdgeModel:
        """Persists a new directed edge to SQLite and hot-updates the in-memory graph."""
        async with aiosqlite.connect(self.db.db_path) as conn:
            await conn.execute("PRAGMA foreign_keys = ON;")
            await conn.execute(
                """
                INSERT INTO graph_edges (id, source_node_id, target_node_id, relation_type, weight, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (edge.id, edge.source_node_id, edge.target_node_id, edge.relation_type, edge.weight, edge.metadata_json, edge.created_at)
            )
            await conn.commit()

        # Hot-update in-memory graph without full rebuild
        self.graph.add_edge(
            edge.source_node_id,
            edge.target_node_id,
            edge_id=edge.id,
            relation_type=edge.relation_type,
            weight=edge.weight
        )
        return edge

    def compute_foundation_scores(self) -> Dict[str, float]:
        """
        Computes PageRank-based Foundation Scores for each node.
        High-scoring nodes are epistemic keystones: 
        many other conclusions depend on them directly or transitively.
        """
        if len(self.graph.nodes) == 0:
            return {}
        try:
            # Use pure-Python PageRank (no scipy dependency) for memory-constrained hardware
            scores = nx.pagerank(self.graph, alpha=0.85, weight="weight", max_iter=200, tol=1.0e-6)
        except (nx.PowerIterationFailedConvergence, ImportError, ModuleNotFoundError):
            # Fallback: in-degree centrality when scipy is unavailable
            total = max(self.graph.number_of_nodes(), 1)
            scores = {n: self.graph.in_degree(n) / total for n in self.graph.nodes}
        return {k: round(v, 6) for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}

    def compute_impact_cascade(self, node_id: str) -> Dict[str, Any]:
        """
        Impact Radar: Given a node_id (a claim or assumption being challenged),
        traverses the directed graph to find all reachable downstream
        conclusions/hypotheses/beliefs that become vulnerable.

        Returns cascade details including depth layers and total affected count.
        """
        if node_id not in self.graph:
            return {"node_id": node_id, "affected_nodes": [], "cascade_depth": 0, "total_affected": 0}

        # BFS to find all reachable downstream descendants
        affected: Dict[str, int] = {}  # node_id -> depth from root
        queue = [(node_id, 0)]
        visited: Set[str] = {node_id}

        while queue:
            current, depth = queue.pop(0)
            for successor in self.graph.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    affected[successor] = depth + 1
                    queue.append((successor, depth + 1))

        # Build impact layers grouped by cascade depth
        max_depth = max(affected.values()) if affected else 0
        layers: List[List[str]] = [[] for _ in range(max_depth + 1)]
        for n_id, depth in affected.items():
            layers[depth].append(n_id)

        # Compute vulnerability score per affected node (decay with depth)
        vulnerability_scores = {
            n_id: round(1.0 / (depth + 1), 4)
            for n_id, depth in affected.items()
        }

        return {
            "node_id": node_id,
            "affected_nodes": list(affected.keys()),
            "cascade_depth": max_depth,
            "total_affected": len(affected),
            "depth_layers": layers,
            "vulnerability_scores": vulnerability_scores
        }

    def serialize_for_frontend(self) -> Dict[str, Any]:
        """
        Serializes the graph into a JSON-compatible format for
        the interactive frontend visualization canvas (Sigma.js / PixiJS).
        """
        nodes = []
        for n_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": n_id,
                "label": attrs.get("title", n_id[:8]),
                "node_type": attrs.get("node_type", "UNKNOWN"),
                "status": attrs.get("status", "ACTIVE"),
                "confidence_score": attrs.get("confidence_score", 1.0)
            })

        edges = []
        for src, tgt, attrs in self.graph.edges(data=True):
            edges.append({
                "id": attrs.get("edge_id", generate_uuid()),
                "source": src,
                "target": tgt,
                "relation_type": attrs.get("relation_type", "RELATED"),
                "weight": attrs.get("weight", 1.0)
            })

        return {"nodes": nodes, "edges": edges}
