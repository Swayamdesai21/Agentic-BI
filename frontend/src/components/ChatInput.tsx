"use client";

import React, { useState, useRef, useEffect } from "react";
import { Suggestion } from "@/lib/types";

interface ChatInputProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
  suggestions: Suggestion[];
}

export default function ChatInput({ onSubmit, isLoading, suggestions }: ChatInputProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full">
      {/* Suggestion Chips */}
      {suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => {
                if (!isLoading) {
                  onSubmit(s.text);
                }
              }}
              disabled={isLoading}
              className="group flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gray-800/60 border border-gray-700/40
                text-xs text-gray-400 hover:text-white hover:border-indigo-500/40 hover:bg-indigo-500/10
                transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="text-sm">{s.icon}</span>
              <span>{s.text}</span>
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="relative group">
        <div className="relative flex items-end bg-gray-900/70 backdrop-blur-xl border border-gray-700/50 rounded-2xl
          focus-within:border-indigo-500/50 focus-within:shadow-lg focus-within:shadow-indigo-500/10
          transition-all duration-300">
          <textarea
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your data..."
            disabled={isLoading}
            rows={1}
            className="flex-1 bg-transparent text-white placeholder-gray-500 px-5 py-4 pr-14 resize-none
              focus:outline-none text-sm disabled:opacity-50 max-h-32"
            style={{ minHeight: "52px" }}
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute right-3 bottom-3 w-9 h-9 rounded-xl bg-indigo-600 hover:bg-indigo-500
              disabled:bg-gray-700 disabled:cursor-not-allowed flex items-center justify-center
              transition-all duration-200 hover:scale-105 active:scale-95"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
                <path d="M22 2L11 13" />
                <path d="M22 2L15 22L11 13L2 9L22 2Z" />
              </svg>
            )}
          </button>
        </div>
        <p className="text-[10px] text-gray-600 mt-2 text-center">
          Press Enter to send · Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}
