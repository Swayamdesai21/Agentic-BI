"use client";

import React from "react";
import ChartRenderer from "./ChartRenderer";
import { DashboardPanel as PanelType } from "@/lib/types";

interface DashboardPanelProps {
  panel: PanelType;
  onRemove?: (id: string) => void;
}

export default function DashboardPanel({ panel, onRemove }: DashboardPanelProps) {
  const [showSQL, setShowSQL] = React.useState(false);

  return (
    <div className="group bg-gray-900/50 backdrop-blur-xl border border-gray-700/40 rounded-2xl overflow-hidden transition-all duration-300 hover:border-indigo-500/30 hover:shadow-lg hover:shadow-indigo-500/5 animate-slideUp">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800/50 flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-white truncate">
            {panel.chart_config?.title || panel.question}
          </h3>
          <p className="text-xs text-gray-500 mt-1 truncate">{panel.question}</p>
        </div>
        <div className="flex items-center gap-2 ml-3 flex-shrink-0">
          {panel.sql_query && (
            <button
              onClick={() => setShowSQL(!showSQL)}
              className="text-xs px-2.5 py-1 rounded-lg bg-gray-800/80 text-gray-400 hover:text-indigo-400 hover:bg-gray-800 transition-colors"
            >
              {showSQL ? "Hide" : "SQL"}
            </button>
          )}
          {onRemove && (
            <button
              onClick={() => onRemove(panel.id)}
              className="text-gray-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* SQL Toggle */}
      {showSQL && panel.sql_query && (
        <div className="px-6 py-3 bg-gray-950/50 border-b border-gray-800/30">
          <pre className="text-xs text-indigo-300/80 font-mono overflow-x-auto whitespace-pre-wrap">
            {panel.sql_query}
          </pre>
        </div>
      )}

      {/* Error State */}
      {panel.error && (
        <div className="px-6 py-4">
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
            <p className="text-red-400 text-sm">{panel.error}</p>
          </div>
        </div>
      )}

      {/* Chart */}
      {panel.chart_config && !panel.error && (
        <div className="px-4 py-4">
          <ChartRenderer config={panel.chart_config} />
        </div>
      )}

      {/* Narrative */}
      {panel.narrative && !panel.error && (
        <div className="px-6 py-4 border-t border-gray-800/30">
          <div className="flex items-start gap-2.5">
            <span className="text-lg mt-0.5 flex-shrink-0">💡</span>
            <div
              className="text-sm text-gray-400 leading-relaxed prose prose-invert prose-sm max-w-none
                [&_strong]:text-indigo-300 [&_li]:text-gray-400"
              dangerouslySetInnerHTML={{
                __html: panel.narrative
                  .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                  .replace(/\n- /g, "<br/>• ")
                  .replace(/\n/g, "<br/>"),
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
