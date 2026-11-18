import axios from "axios";

const API_BASE = "http://127.0.0.1:8765";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export interface NodeItem {
  id: string;
  title: string;
  content: string;
  node_type?: string;
  confidence_score?: number;
  tags?: string[];
  created_at?: string;
}

export interface SearchResult {
  node_id: string;
  title: string;
  content: string;
  score: number;
}

export interface ContradictionItem {
  id: string;
  node_a_id: string;
  node_b_id: string;
  explanation: string;
  severity: number;
}

export interface SimulationResult {
  toggled_nodes: string[];
  scenario_label: string;
  nodes_affected: number;
  delta_summary: Record<string, any>;
}

export const MindVaultAPI = {
  checkHealth: async () => {
    const res = await api.get("/");
    return res.data;
  },

  getNodes: async (): Promise<NodeItem[]> => {
    const res = await api.get("/nodes");
    return res.data.nodes || [];
  },

  createNode: async (data: { title: string; content: string; confidence_score: number; node_type?: string }) => {
    const res = await api.post("/nodes", {
      title: data.title,
      content: data.content,
      node_type: data.node_type || "CONCEPT",
      confidence_score: data.confidence_score,
    });
    return res.data;
  },

  search: async (query: string, limit = 10): Promise<SearchResult[]> => {
    const res = await api.get("/search", { params: { q: query, top_k: limit } });
    return res.data.results || [];
  },

  getContradictions: async (): Promise<ContradictionItem[]> => {
    const res = await api.get("/contradictions");
    return res.data.contradictions || [];
  },

  getGraphData: async () => {
    const res = await api.get("/graph");
    return res.data;
  },

  askAssistant: async (question: string) => {
    const res = await api.post("/assistant/ask", { question, top_k: 5 });
    return res.data;
  },

  runSimulation: async (nodeId: string, label = "What-If Scenario"): Promise<SimulationResult> => {
    const res = await api.post("/simulation/run", {
      toggled_node_ids: [nodeId],
      scenario_label: label,
    });
    return res.data;
  },
};
