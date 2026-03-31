"""
Pydantic models for the Agentic BI system.
Defines schemas for API requests/responses, chart configs, and agent state.
"""

from __future__ import annotations
from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


# ── API Models ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """User's natural language query."""
    question: str = Field(..., description="Natural language question about the data")
    conversation_id: Optional[str] = Field(None, description="ID for conversation continuity")


# ── Chart Configuration ────────────────────────────────────────────────

class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    TABLE = "table"


class ChartConfig(BaseModel):
    """Pydantic-validated chart configuration."""
    chart_type: ChartType = Field(..., description="Type of chart to render")
    title: str = Field(..., description="Chart title")
    x_key: str = Field("", description="Key for X-axis data")
    y_key: str = Field("", description="Key for Y-axis data")
    data: list[dict[str, Any]] = Field(default_factory=list, description="Chart data points")
    colors: list[str] = Field(
        default_factory=lambda: ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#14b8a6", "#f59e0b"],
        description="Chart color palette"
    )
    x_label: str = Field("", description="X-axis label")
    y_label: str = Field("", description="Y-axis label")


# ── Dashboard Panel ────────────────────────────────────────────────────

class DashboardPanel(BaseModel):
    """A single dashboard panel combining chart + narrative."""
    id: str = Field(..., description="Unique panel ID")
    question: str = Field(..., description="Original user question")
    sql_query: str = Field("", description="Generated SQL query")
    chart_config: Optional[ChartConfig] = Field(None, description="Chart configuration")
    narrative: str = Field("", description="Plain-English insight summary")
    error: Optional[str] = Field(None, description="Error message if any")


# ── SSE Event Types ────────────────────────────────────────────────────

class SSEEventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_THINKING = "agent_thinking"
    SQL_GENERATED = "sql_generated"
    SQL_VALIDATED = "sql_validated"
    SQL_ERROR = "sql_error"
    DATA_READY = "data_ready"
    CHART_CONFIG = "chart_config"
    NARRATIVE = "narrative"
    COMPLETE = "complete"
    ERROR = "error"


class SSEEvent(BaseModel):
    """Server-Sent Event payload."""
    event: SSEEventType
    data: dict[str, Any] = Field(default_factory=dict)
    agent: str = Field("", description="Which agent is currently active")
