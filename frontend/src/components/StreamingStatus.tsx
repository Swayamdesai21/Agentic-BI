"use client";

import React from "react";
import { AgentProgress } from "@/lib/types";

interface StreamingStatusProps {
  agents: AgentProgress[];
  isStreaming: boolean;
}

const agentIcons: Record<string, string> = {
  "Query Agent": "🔍",
  "Validator Agent": "✅",
  "Visualization Agent": "📊",
  "Narrative Agent": "📝",
  System: "⚡",
};

const statusColors: Record<string, string> = {
  idle: "bg-gray-700",
  working: "bg-indigo-500 animate-pulse",
  done: "bg-emerald-500",
  error: "bg-red-500",
};

export default function StreamingStatus({ agents, isStreaming }: StreamingStatusProps) {
  if (!isStreaming && agents.every((a) => a.status === "idle")) return null;

  return (
    <div className="bg-gray-900/60 backdrop-blur-xl border border-gray-700/40 rounded-2xl p-5 mb-6 animate-fadeIn">
      <div className="flex items-center gap-2 mb-4">
        <div className="relative">
          <div className="w-2.5 h-2.5 bg-indigo-500 rounded-full" />
          {isStreaming && (
            <div className="absolute inset-0 w-2.5 h-2.5 bg-indigo-500 rounded-full animate-ping" />
          )}
        </div>
        <span className="text-sm font-medium text-gray-300">
          {isStreaming ? "Agents working..." : "Pipeline complete"}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {agents.map((agent, i) => (
          <React.Fragment key={agent.name}>
            <div className="flex flex-col items-center gap-1.5 min-w-[80px]">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg transition-all duration-500 ${
                  agent.status === "working"
                    ? "bg-indigo-500/20 border-2 border-indigo-500 scale-110 shadow-lg shadow-indigo-500/20"
                    : agent.status === "done"
                    ? "bg-emerald-500/20 border-2 border-emerald-500"
                    : agent.status === "error"
                    ? "bg-red-500/20 border-2 border-red-500"
                    : "bg-gray-800 border border-gray-700"
                }`}
              >
                {agentIcons[agent.name] || "🤖"}
              </div>
              <span className="text-[10px] text-gray-500 font-medium text-center leading-tight">
                {agent.name.replace(" Agent", "")}
              </span>
              <div className={`w-1.5 h-1.5 rounded-full ${statusColors[agent.status]}`} />
            </div>
            {i < agents.length - 1 && (
              <div
                className={`h-0.5 w-6 rounded transition-colors duration-500 ${
                  agent.status === "done" ? "bg-emerald-500/60" : "bg-gray-700"
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {agents.find((a) => a.status === "working")?.message && (
        <p className="mt-3 text-xs text-gray-500 italic pl-1">
          {agents.find((a) => a.status === "working")?.message}
        </p>
      )}
    </div>
  );
}
