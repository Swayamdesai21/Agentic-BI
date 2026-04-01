"use client";

import React, { useState, useEffect, useCallback } from "react";
import ChatInput from "@/components/ChatInput";
import DashboardPanelComponent from "@/components/DashboardPanel";
import StreamingStatus from "@/components/StreamingStatus";
import { streamQuery, fetchSuggestions, checkHealth } from "@/lib/sse-client";
import { DashboardPanel, Suggestion, AgentProgress, SSEEvent } from "@/lib/types";

const DEFAULT_AGENTS: AgentProgress[] = [
  { name: "Query Agent", status: "idle", message: "" },
  { name: "Validator Agent", status: "idle", message: "" },
  { name: "Visualization Agent", status: "idle", message: "" },
  { name: "Narrative Agent", status: "idle", message: "" },
];

export default function Home() {
  const [panels, setPanels] = useState<DashboardPanel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [agents, setAgents] = useState<AgentProgress[]>(DEFAULT_AGENTS);
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [queryCount, setQueryCount] = useState(0);

  useEffect(() => {
    fetchSuggestions().then(setSuggestions);
    checkHealth().then((h) => setIsHealthy(h.status === "healthy" && h.groq_configured));
  }, []);

  const updateAgentStatus = useCallback((agentName: string, status: "idle" | "working" | "done" | "error", message: string = "") => {
    setAgents((prev) =>
      prev.map((a) => (a.name === agentName ? { ...a, status, message } : a))
    );
  }, []);

  const handleQuery = useCallback(
    async (question: string) => {
      setIsLoading(true);
      setAgents(DEFAULT_AGENTS.map((a) => ({ ...a, status: "idle", message: "" })));

      await streamQuery(question, {
        onEvent: (event: SSEEvent) => {
          const agentName = event.agent;
          switch (event.event) {
            case "agent_start":
            case "agent_thinking":
              updateAgentStatus(agentName, "working", String(event.data?.message || ""));
              break;
            case "sql_generated":
              updateAgentStatus("Query Agent", "done", "SQL generated");
              break;
            case "sql_validated":
              updateAgentStatus("Validator Agent", "done", `${event.data?.row_count || 0} rows`);
              break;
            case "sql_error":
              updateAgentStatus("Validator Agent", "error", String(event.data?.error || "Error"));
              updateAgentStatus("Query Agent", "working", "Retrying...");
              break;
            case "chart_config":
              updateAgentStatus("Visualization Agent", "done", "Chart ready");
              break;
            case "narrative":
              updateAgentStatus("Narrative Agent", "done", "Insights generated");
              break;
            case "complete":
              setAgents((prev) => prev.map((a) => (a.status === "idle" ? { ...a, status: "done" } : a)));
              break;
          }
        },
        onPanel: (panel: DashboardPanel) => {
          setPanels((prev) => [panel, ...prev]);
          setQueryCount((c) => c + 1);
        },
        onError: (error: string) => {
          const errorPanel: DashboardPanel = {
            id: `error-${Date.now()}`,
            question,
            sql_query: "",
            chart_config: null,
            narrative: "",
            error,
          };
          setPanels((prev) => [errorPanel, ...prev]);
        },
        onComplete: () => {
          setIsLoading(false);
        },
      });

      setIsLoading(false);
    },
    [updateAgentStatus]
  );

  const removePanel = useCallback((id: string) => {
    setPanels((prev) => prev.filter((p) => p.id !== id));
  }, []);

  return (
    <main className="min-h-screen relative overflow-hidden">
      {/* Background Effects */}
      <div className="glow-orb w-96 h-96 bg-indigo-600 top-[-200px] left-[-100px] fixed" />
      <div className="glow-orb w-80 h-80 bg-purple-600 bottom-[-150px] right-[-50px] fixed" />
      <div className="glow-orb w-64 h-64 bg-teal-500 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 fixed opacity-[0.05]" />

      <div className="relative z-10 max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <header className="text-center mb-10 animate-fadeIn">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 animate-float">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
                <path d="M21 12c0 1.4-.5 2.6-1.3 3.6" />
                <path d="M3 12c0-1.4.5-2.6 1.3-3.6" />
                <path d="M12 3c1.4 0 2.6.5 3.6 1.3" />
                <path d="M12 21c-1.4 0-2.6-.5-3.6-1.3" />
                <circle cx="12" cy="12" r="3" />
                <path d="M12 1v4M12 19v4M1 12h4M19 12h4" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold">
              <span className="animate-gradient-text">Agentic BI</span>
            </h1>
          </div>
          <p className="text-gray-500 text-sm max-w-md mx-auto">
            Ask questions in plain English. AI agents build live dashboards for you.
          </p>

          {/* Status Indicators */}
          <div className="flex items-center justify-center gap-4 mt-4">
            {isHealthy !== null && (
              <div className={`flex items-center gap-1.5 text-xs ${isHealthy ? "text-emerald-500" : "text-amber-500"}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${isHealthy ? "bg-emerald-500" : "bg-amber-500 animate-pulse"}`} />
                {isHealthy ? "Backend Connected" : "Backend Offline — Start the server"}
              </div>
            )}
            {queryCount > 0 && (
              <div className="text-xs text-gray-600">
                {queryCount} {queryCount === 1 ? "query" : "queries"} · {panels.length} {panels.length === 1 ? "panel" : "panels"}
              </div>
            )}
          </div>
        </header>

        {/* Chat Input */}
        <section className="max-w-5xl mx-auto mb-8 animate-fadeIn" style={{ animationDelay: "0.1s" }}>
          <ChatInput
            onSubmit={handleQuery}
            isLoading={isLoading}
            suggestions={panels.length === 0 ? suggestions : []}
          />
        </section>

        {/* Streaming Status */}
        <section className="max-w-5xl mx-auto">
          <StreamingStatus agents={agents} isStreaming={isLoading} />
        </section>

        {/* Dashboard Panels */}
        {panels.length > 0 && (
          <section className="mt-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-gray-300">
                Dashboard
              </h2>
              {panels.length > 1 && (
                <button
                  onClick={() => setPanels([])}
                  className="text-xs text-gray-600 hover:text-red-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-500/10"
                >
                  Clear all
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {panels.map((panel) => (
                <DashboardPanelComponent
                  key={panel.id}
                  panel={panel}
                  onRemove={removePanel}
                />
              ))}
            </div>
          </section>
        )}

        {/* Empty State */}
        {panels.length === 0 && !isLoading && (
          <section className="text-center mt-16 animate-fadeIn" style={{ animationDelay: "0.2s" }}>
            <div className="space-y-4 max-w-2xl mx-auto">
              <div className="text-4xl animate-float" style={{ animationDelay: "0.5s" }}>🎯</div>
              <h3 className="text-lg font-medium text-gray-400">Ready to explore your data</h3>
              <p className="text-sm text-gray-600">
                Type a question above or click a suggestion to get started.
                Each query creates a live dashboard panel with charts and insights.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 text-left">
                {[
                  { icon: "🔍", label: "Natural Language", desc: "Ask in plain English" },
                  { icon: "🤖", label: "Multi-Agent", desc: "4 AI agents collaborate" },
                  { icon: "📊", label: "Auto Charts", desc: "Smart visualization" },
                  { icon: "💡", label: "AI Insights", desc: "Key findings explained" },
                ].map((f, i) => (
                  <div key={i} className="glass rounded-xl p-3.5 glass-hover transition-all">
                    <span className="text-lg">{f.icon}</span>
                    <p className="text-xs font-medium text-gray-300 mt-1.5">{f.label}</p>
                    <p className="text-[10px] text-gray-600">{f.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Footer */}
        <footer className="text-center mt-16 pb-8">
          <p className="text-[11px] text-gray-700">
            Powered by LangGraph · Groq · Next.js · Recharts
          </p>
        </footer>
      </div>
    </main>
  );
}
