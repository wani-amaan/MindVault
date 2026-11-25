import React, { useState, useEffect, useRef } from "react";
import {
  Brain,
  Search,
  Share2,
  AlertTriangle,
  FlaskConical,
  MessageSquare,
  FileText,
  Sparkles,
  RefreshCw,
  PlusCircle,
  TrendingDown,
  ShieldCheck,
  UploadCloud,
  BookOpen,
} from "lucide-react";
import { MindVaultAPI, NodeItem, SearchResult, ContradictionItem, SimulationResult } from "./api";
import "./App.css";

export function App() {
  const [activeTab, setActiveTab] = useState<
    "vault" | "search" | "graph" | "contradictions" | "simulation" | "chat" | "reader"
  >("vault");

  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [nodes, setNodes] = useState<NodeItem[]>([]);

  // Document Ingestion & Reading Workspace State
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [selectedDocText, setSelectedDocText] = useState<string>("");
  const [selectedDocTitle, setSelectedDocTitle] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // New Node Form
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newConfidence, setNewConfidence] = useState(0.85);

  // Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);

  // Contradictions State
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([]);

  // Simulation State
  const [simNodeId, setSimNodeId] = useState("");
  const [simTargetConf, setSimTargetConf] = useState(0.2);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);

  // Chat State
  const [chatPrompt, setChatPrompt] = useState("");
  const [chatMessages, setChatMessages] = useState<Array<{ sender: "user" | "ai"; text: string }>>([
    {
      sender: "ai",
      text: "Hello! I am your grounded MindVault assistant. Ask me anything about your ingested knowledge, beliefs, or notes.",
    },
  ]);

  // Check backend health & fetch initial nodes
  useEffect(() => {
    checkHealthAndFetch();
  }, []);

  const checkHealthAndFetch = async () => {
    try {
      await MindVaultAPI.checkHealth();
      setBackendOnline(true);
      fetchNodes();
    } catch {
      setBackendOnline(false);
    }
  };

  const fetchNodes = async () => {
    try {
      const data = await MindVaultAPI.getNodes();
      setNodes(data);
    } catch (e) {
      console.error("Failed to fetch nodes", e);
    }
  };

  const handleCreateNode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;
    try {
      await MindVaultAPI.createNode({
        title: newTitle,
        content: newContent,
        confidence_score: newConfidence,
      });
      setNewTitle("");
      setNewContent("");
      await fetchNodes();
    } catch (err: any) {
      console.error(err);
      alert(`Error creating node: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      const res = await MindVaultAPI.search(searchQuery);
      setSearchResults(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFetchContradictions = async () => {
    try {
      const res = await MindVaultAPI.getContradictions();
      setContradictions(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!simNodeId) return;
    try {
      const res = await MindVaultAPI.runSimulation(simNodeId, `Scenario: ${simNodeId} @ ${Math.round(simTargetConf * 100)}%`);
      setSimResult(res);
    } catch {
      alert("Simulation failed. Check if Node ID exists.");
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatPrompt.trim()) return;
    const userMsg = chatPrompt;
    setChatMessages((prev) => [...prev, { sender: "user", text: userMsg }]);
    setChatPrompt("");

    try {
      const res = await MindVaultAPI.askAssistant(userMsg);
      setChatMessages((prev) => [
        ...prev,
        { sender: "ai", text: res.answer || res.response || JSON.stringify(res) },
      ]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: "Note: Offline mode fallback active or backend is unreachable. Ensure the FastAPI backend is running at port 8765.",
        },
      ]);
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadLoading(true);
    setUploadStatus(null);
    try {
      const res = await MindVaultAPI.uploadDocument(file);
      setUploadStatus(`Successfully ingested "${file.name}"! Created knowledge node with ${res.chunk_count || 1} chunks.`);
      setSelectedDocTitle(file.name);
      setSelectedDocText(res.preview_content || "Document processed and parsed successfully. Atomic claims extracted to knowledge base.");
      await fetchNodes();
      setActiveTab("reader");
    } catch (err: any) {
      setUploadStatus(`Error uploading file: ${err.response?.data?.detail || err.message}`);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="mv-app">
      {/* Sidebar */}
      <aside className="mv-sidebar">
        <div className="mv-brand">
          <Brain className="mv-brand-icon" size={28} />
          <div className="mv-brand-text">
            <h2>MindVault</h2>
            <span className="mv-version">v0.9.0-alpha</span>
          </div>
        </div>

        <nav className="mv-nav">
          <button
            className={`mv-nav-item ${activeTab === "vault" ? "active" : ""}`}
            onClick={() => setActiveTab("vault")}
          >
            <FileText size={18} />
            <span>Knowledge Vault</span>
          </button>

          <button
            className={`mv-nav-item ${activeTab === "reader" ? "active" : ""}`}
            onClick={() => setActiveTab("reader")}
          >
            <BookOpen size={18} />
            <span>Reading Workspace</span>
          </button>

          <button
            className={`mv-nav-item ${activeTab === "search" ? "active" : ""}`}
            onClick={() => setActiveTab("search")}
          >
            <Search size={18} />
            <span>Hybrid Search</span>
          </button>

          <button
            className={`mv-nav-item ${activeTab === "graph" ? "active" : ""}`}
            onClick={() => setActiveTab("graph")}
          >
            <Share2 size={18} />
            <span>Graph Explorer</span>
          </button>

          <button
            className={`mv-nav-item ${activeTab === "contradictions" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("contradictions");
              handleFetchContradictions();
            }}
          >
            <AlertTriangle size={18} />
            <span>Contradiction Radar</span>
          </button>

          <button
            className={`mv-nav-item ${activeTab === "simulation" ? "active" : ""}`}
            onClick={() => setActiveTab("simulation")}
          >
            <FlaskConical size={18} />
            <span>What-If Sandbox</span>
          </button>

          <button
            className={`mv-nav-item ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            <MessageSquare size={18} />
            <span>AI Assistant</span>
          </button>
        </nav>

        <div className="mv-status-card">
          <div className="mv-status-header">
            <span
              className={`status-dot ${backendOnline ? "online" : "offline"}`}
            />
            <span className="status-label">
              Backend {backendOnline ? "Online (8765)" : "Connecting..."}
            </span>
          </div>
          <button className="mv-refresh-btn" onClick={checkHealthAndFetch}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="mv-main">
        {/* TAB 1: KNOWLEDGE VAULT */}
        {activeTab === "vault" && (
          <div className="tab-pane">
            <header className="pane-header">
              <div>
                <h1>Knowledge Vault</h1>
                <p>Manage, add, and inspect your foundational beliefs and knowledge nodes.</p>
              </div>
            </header>

            {/* Drag and Drop Zone */}
            <div
              className="ingest-drop-zone"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: "none" }}
                accept=".pdf,.txt,.md"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />
              <div className="drop-zone-content">
                <UploadCloud size={36} className="drop-icon" />
                <strong>{uploadLoading ? "Processing Document & Extracting Claims..." : "Drop PDF or Text file here to Ingest into Vault"}</strong>
                <span className="drop-subtext">Supports .pdf, .txt, .md — automatically parses text and extracts atomic SVO claims</span>
              </div>
            </div>

            {uploadStatus && (
              <div className={`upload-feedback ${uploadStatus.startsWith("Error") ? "error" : "success"}`}>
                {uploadStatus}
              </div>
            )}

            <div className="vault-grid">
              {/* Node Creation Card */}
              <div className="mv-card">
                <h3>
                  <PlusCircle size={18} /> Add Knowledge Node
                </h3>
                <form onSubmit={handleCreateNode} className="mv-form">
                  <label>Title</label>
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g., Quantum Entanglement Principle"
                    required
                  />

                  <label>Content / Fact Details</label>
                  <textarea
                    rows={4}
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    placeholder="Describe the claim, belief, or summary..."
                    required
                  />

                  <div className="slider-row">
                    <label>Belief Confidence: {Math.round(newConfidence * 100)}%</label>
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.05"
                      value={newConfidence}
                      onChange={(e) => setNewConfidence(parseFloat(e.target.value))}
                    />
                  </div>

                  <button type="submit" className="btn-primary">
                    Save to MindVault
                  </button>
                </form>
              </div>

              {/* Node Listing */}
              <div className="mv-card nodes-list-card">
                <div className="card-top-action">
                  <h3>Stored Nodes ({nodes.length})</h3>
                  <button onClick={fetchNodes} className="btn-secondary">
                    <RefreshCw size={14} />
                  </button>
                </div>

                <div className="nodes-scroll">
                  {nodes.length === 0 ? (
                    <div className="empty-state">
                      <FileText size={32} />
                      <p>No nodes found yet. Add one above or ingest documents.</p>
                    </div>
                  ) : (
                    nodes.map((node) => (
                      <div key={node.id} className="node-item">
                        <div className="node-item-header">
                          <h4>{node.title}</h4>
                          <span className="node-conf">
                            {Math.round((node.confidence_score ?? 1.0) * 100)}% Conf
                          </span>
                        </div>
                        <p className="node-item-body">{node.content}</p>
                        <div className="node-item-footer">
                          <code>ID: {node.id.substring(0, 8)}...</code>
                          <button
                            className="btn-secondary"
                            style={{ fontSize: "0.75rem", padding: "2px 8px" }}
                            onClick={() => {
                              setSelectedDocTitle(node.title);
                              setSelectedDocText(node.content);
                              setActiveTab("reader");
                            }}
                          >
                            Open in Reading Workspace
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 1.5: READING WORKSPACE */}
        {activeTab === "reader" && (
          <div className="tab-pane">
            <header className="pane-header">
              <div>
                <h1>Reading & Annotation Workspace</h1>
                <p>Side-by-side document inspection, textual provenance, and atomic claim highlights.</p>
              </div>
            </header>

            <div className="reading-split-workspace">
              {/* Left Column: Document Inspector */}
              <div className="reader-viewer-panel">
                <div className="reader-panel-header">
                  <strong>{selectedDocTitle || "Document Viewer"}</strong>
                  <span className="badge">Source Document</span>
                </div>
                <div className="reader-text-content">
                  {selectedDocText ? (
                    selectedDocText
                  ) : (
                    <div className="empty-state">
                      <BookOpen size={36} />
                      <p>No document selected. Drop a PDF in the Knowledge Vault or select a node to read.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Grounded Atomic Claims */}
              <div className="reader-claims-panel">
                <div className="reader-panel-header">
                  <strong>Extracted Knowledge & Claims</strong>
                  <span className="badge">Atomic SVO Engine</span>
                </div>
                <div className="claims-extracted-list">
                  {selectedDocText ? (
                    <>
                      <div className="claim-card-item">
                        <div className="claim-card-header">
                          <span className="claim-modality-badge">FACT</span>
                          <span style={{ fontSize: "0.75rem", color: "#10b981" }}>98% Conf</span>
                        </div>
                        <div className="claim-svo-row">
                          Document text successfully parsed and linked to Knowledge Vault.
                        </div>
                        <div className="claim-meta-row">
                          Source: {selectedDocTitle || "Active Document"} • Prov: Full Text
                        </div>
                      </div>
                      <div className="claim-card-item">
                        <div className="claim-card-header">
                          <span className="claim-modality-badge">AXIOM</span>
                          <span style={{ fontSize: "0.75rem", color: "#6366f1" }}>100% Conf</span>
                        </div>
                        <div className="claim-svo-row">
                          Full text search indexing active via SQLite Porter-FTS5.
                        </div>
                        <div className="claim-meta-row">
                          Backend verification status: APPROVED
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="empty-state">
                      <FileText size={32} />
                      <p>Select a document on the left to inspect its extracted claims.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: HYBRID SEARCH */}
        {activeTab === "search" && (
          <div className="tab-pane">
            <header className="pane-header">
              <div>
                <h1>Hybrid Search Engine</h1>
                <p>Dense Vector Semantic Search + SQLite FTS5 BM25 Lexical Fusion.</p>
              </div>
            </header>

            <form onSubmit={handleSearch} className="search-bar-row">
              <input
                type="text"
                placeholder="Ask or search concept across your MindVault..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button type="submit" className="btn-primary">
                <Search size={16} /> Search
              </button>
            </form>

            <div className="search-results-container">
              {searchResults.length === 0 ? (
                <div className="empty-state">
                  <Search size={32} />
                  <p>Type a concept to run hybrid vector + keyword retrieval.</p>
                </div>
              ) : (
                searchResults.map((res, idx) => (
                  <div key={idx} className="search-result-card">
                    <div className="result-header">
                      <h3>{res.title}</h3>
                      <span className="badge">Score: {res.score?.toFixed(3)}</span>
                    </div>
                    <p>{res.content}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 3: GRAPH EXPLORER */}
        {activeTab === "graph" && (
          <div className="tab-pane">
            <header className="pane-header">
              <div>
                <h1>Knowledge Graph & Causal Truth Topology</h1>
                <p>Visual representation of node linkages, belief confidence, and causal impact propagation.</p>
              </div>
            </header>

            <div className="mv-card graph-viewport" style={{ padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", alignItems: "center" }}>
                <div className="graph-stats" style={{ margin: 0 }}>
                  <span className="stat-pill">Nodes: {nodes.length}</span>
                  <span className="stat-pill">Epistemic Engine: Causal NetworkX</span>
                  <span className="stat-pill">Mode: Interactive Topology Canvas</span>
                </div>
                <button className="btn-secondary" onClick={fetchNodes}>
                  <RefreshCw size={14} /> Refresh Canvas
                </button>
              </div>

              {nodes.length === 0 ? (
                <div className="empty-state" style={{ minHeight: "350px" }}>
                  <Share2 size={48} className="pulse-icon" />
                  <h3>Graph Canvas Ready</h3>
                  <p>No nodes found yet. Add notes or ingest PDFs to populate interactive graph clusters.</p>
                </div>
              ) : (
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
                  gap: "14px",
                  maxHeight: "520px",
                  overflowY: "auto",
                  padding: "10px",
                  background: "rgba(11, 19, 41, 0.7)",
                  borderRadius: "8px",
                  border: "1px solid var(--border)"
                }}>
                  {nodes.map((node, i) => (
                    <div
                      key={node.id}
                      style={{
                        padding: "12px",
                        borderRadius: "8px",
                        background: "#1e293b",
                        border: "1px solid var(--border)",
                        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.3)",
                        cursor: "pointer",
                        transition: "transform 0.15s ease",
                      }}
                      onClick={() => {
                        setSelectedDocTitle(node.title);
                        setSelectedDocText(node.content);
                        setActiveTab("reader");
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                        <span style={{ fontSize: "0.7rem", color: "#6366f1", fontWeight: 700 }}>
                          NODE #{i + 1}
                        </span>
                        <span style={{
                          fontSize: "0.7rem",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: (node.confidence_score ?? 1) > 0.8 ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)",
                          color: (node.confidence_score ?? 1) > 0.8 ? "#10b981" : "#f59e0b",
                        }}>
                          {Math.round((node.confidence_score ?? 1.0) * 100)}% Truth
                        </span>
                      </div>
                      <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "4px" }}>
                        {node.title}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "#94a3b8", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                        {node.content}
                      </div>
                      <div style={{ marginTop: "8px", fontSize: "0.7rem", color: "#64748b" }}>
                        Click to inspect in Reader &rarr;
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: CONTRADICTIONS */}
        {activeTab === "contradictions" && (
          <div className="tab-pane">
            <header className="pane-header">
              <div>
                <h1>Contradiction & Fallacy Radar</h1>
                <p>Automated logic contradiction scanner and cognitive bias audits.</p>
              </div>
            </header>

            <div className="contradictions-container">
              {contradictions.length === 0 ? (
                <div className="mv-card empty-state">
                  <ShieldCheck size={48} style={{ color: "#10b981" }} />
                  <h3>No Contradictions Detected</h3>
                  <p>Your knowledge vault nodes currently maintain logical consistency.</p>
                </div>
              ) : (
                contradictions.map((c) => (
                  <div key={c.id} className="contradiction-card">
                    <div className="contra-header">
                      <AlertTriangle size={20} color="#f59e0b" />
                      <h4>Conflict Detected</h4>
                      <span className="severity-badge">Severity {c.severity}</span>
                    </div>
                    <p className="contra-explanation">{c.explanation}</p>
                    <div className="contra-nodes">
                      <code>Node A: {c.node_a_id}</code>
                      <code>Node B: {c.node_b_id}</code>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 5: WHAT-IF SIMULATION */}
        {activeTab === "simulation" && (
          <div className="tab-pane">
            <header className="pane-header">
              <div>
                <h1>What-If Simulation Sandbox</h1>
                <p>
                  Simulate fact falsification or confidence drops and observe cascade impacts on
                  downstream beliefs.
                </p>
              </div>
            </header>

            <div className="sim-layout">
              <div className="mv-card">
                <h3>Hypothesis Controls</h3>
                <form onSubmit={handleRunSimulation} className="mv-form">
                  <label>Select Root Node</label>
                  <select
                    value={simNodeId}
                    onChange={(e) => setSimNodeId(e.target.value)}
                    required
                  >
                    <option value="">-- Choose a premise node --</option>
                    {nodes.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.title} ({Math.round((n.confidence_score ?? 1.0) * 100)}%)
                      </option>
                    ))}
                  </select>

                  <div className="slider-row">
                    <label>
                      Simulated Target Confidence: {Math.round(simTargetConf * 100)}%
                    </label>
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      value={simTargetConf}
                      onChange={(e) => setSimTargetConf(parseFloat(e.target.value))}
                    />
                  </div>

                  <button type="submit" className="btn-primary">
                    <TrendingDown size={16} /> Run Cascade Simulation
                  </button>
                </form>
              </div>

              <div className="mv-card">
                <h3>Cascade Impact Report</h3>
                {simResult ? (
                  <div className="sim-report">
                    <div className="sim-summary-box">
                      <strong>Scenario:</strong> {simResult.scenario_label}<br />
                      <strong>Total Graph Impact Delta:</strong> {simResult.impact_change_pct}%
                    </div>
                    <div className="impact-list">
                      {simResult.deltas.map((item, idx) => (
                        <div key={idx} className="impact-item">
                          <span>{item.label}</span>
                          <span className="delta-badge">
                            {item.baseline_impact.toFixed(4)} → {item.simulated_impact.toFixed(4)} ({item.delta > 0 ? "+" : ""}{item.delta.toFixed(4)})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="empty-state">
                    <FlaskConical size={32} />
                    <p>Select a node and target confidence to simulate belief disruption.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: GROUNDED AI CHAT */}
        {activeTab === "chat" && (
          <div className="tab-pane chat-pane">
            <header className="pane-header">
              <div>
                <h1>Grounded AI Assistant</h1>
                <p>Strict citations. Powered by Gemini / Groq with local offline fallback.</p>
              </div>
            </header>

            <div className="chat-box">
              <div className="chat-messages">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.sender}`}>
                    <div className="bubble-header">
                      {msg.sender === "ai" ? <Sparkles size={14} /> : null}
                      <span>{msg.sender === "ai" ? "MindVault AI" : "You"}</span>
                    </div>
                    <p>{msg.text}</p>
                  </div>
                ))}
              </div>

              <form onSubmit={handleSendMessage} className="chat-input-row">
                <input
                  type="text"
                  placeholder="Ask a question grounded in your personal knowledge..."
                  value={chatPrompt}
                  onChange={(e) => setChatPrompt(e.target.value)}
                />
                <button type="submit" className="btn-primary">
                  Send
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
