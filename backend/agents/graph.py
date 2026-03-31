"""
LangGraph State Graph: Orchestrates the full agent pipeline.

Flow: START → query_agent → validator_agent → (retry loop) → viz_agent → narrative_agent → END
"""

from __future__ import annotations
import asyncio
import uuid
from typing import Any, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END

from agents.query_agent import run_query_agent
from agents.validator_agent import run_validator_agent
from agents.viz_agent import run_viz_agent
from agents.narrative_agent import run_narrative_agent
from schema_rag import schema_rag
from models import ChartConfig, DashboardPanel, SSEEvent, SSEEventType


# ── State Definition ────────────────────────────────────────────────────

class AgentState(TypedDict):
    """State passed between agents in the graph."""
    question: str
    schema_context: str
    sql_query: str
    sql_error: str
    retry_count: int
    max_retries: int
    data: list[dict]
    columns: list[str]
    chart_config: Optional[dict]
    narrative: str
    error: Optional[str]
    events: list[dict]  # SSE events to stream


def add_event(state: AgentState, event_type: SSEEventType, agent: str, data: dict = None) -> None:
    """Add an SSE event to the state."""
    state["events"].append({
        "event": event_type.value,
        "agent": agent,
        "data": data or {}
    })


# ── Node Functions ──────────────────────────────────────────────────────

async def query_node(state: AgentState) -> AgentState:
    """Generate SQL from natural language."""
    add_event(state, SSEEventType.AGENT_START, "Query Agent", {
        "message": "Analyzing your question and generating SQL..."
    })

    error_context = ""
    if state.get("sql_error"):
        error_context = f"""
PREVIOUS ATTEMPT FAILED with error:
{state['sql_error']}

Previous SQL that failed:
{state.get('sql_query', '')}

Please fix the SQL query to address this error. Generate a corrected query."""

    try:
        sql = await run_query_agent(
            question=state["question"],
            schema_context=state["schema_context"],
            error_context=error_context
        )
        state["sql_query"] = sql
        add_event(state, SSEEventType.SQL_GENERATED, "Query Agent", {
            "sql": sql,
            "retry": state["retry_count"]
        })
    except Exception as e:
        state["error"] = f"Query Agent failed: {str(e)}"
        add_event(state, SSEEventType.ERROR, "Query Agent", {"error": str(e)})

    return state


async def validator_node(state: AgentState) -> AgentState:
    """Validate and execute the SQL query."""
    if state.get("error"):
        return state

    add_event(state, SSEEventType.AGENT_THINKING, "Validator Agent", {
        "message": "Validating and executing SQL query..."
    })

    result = await run_validator_agent(state["sql_query"])

    if result["valid"]:
        state["data"] = result["data"]
        state["columns"] = result["columns"]
        state["sql_error"] = ""
        add_event(state, SSEEventType.SQL_VALIDATED, "Validator Agent", {
            "row_count": len(result["data"]),
            "columns": result["columns"],
            "warning": result.get("warning", "")
        })
    else:
        state["sql_error"] = result["error"]
        state["retry_count"] = state.get("retry_count", 0) + 1
        add_event(state, SSEEventType.SQL_ERROR, "Validator Agent", {
            "error": result["error"],
            "retry": state["retry_count"]
        })

    return state


def should_retry(state: AgentState) -> str:
    """Decide whether to retry SQL generation or proceed."""
    if state.get("error"):
        return "end"
    if state["sql_error"] and state["retry_count"] < state.get("max_retries", 3):
        return "retry"
    if state["sql_error"]:
        # Max retries exceeded
        state["error"] = f"SQL generation failed after {state['retry_count']} attempts: {state['sql_error']}"
        return "end"
    return "continue"


async def viz_node(state: AgentState) -> AgentState:
    """Generate chart configuration."""
    if state.get("error"):
        return state

    add_event(state, SSEEventType.AGENT_START, "Visualization Agent", {
        "message": "Selecting optimal chart type..."
    })

    try:
        chart_config = await run_viz_agent(
            question=state["question"],
            data=state["data"],
            columns=state["columns"]
        )
        state["chart_config"] = chart_config.model_dump()
        add_event(state, SSEEventType.CHART_CONFIG, "Visualization Agent", {
            "chart_config": chart_config.model_dump()
        })
    except Exception as e:
        state["error"] = f"Viz Agent failed: {str(e)}"
        add_event(state, SSEEventType.ERROR, "Visualization Agent", {"error": str(e)})

    return state


async def narrative_node(state: AgentState) -> AgentState:
    """Generate insight narrative."""
    if state.get("error"):
        return state

    add_event(state, SSEEventType.AGENT_START, "Narrative Agent", {
        "message": "Generating insights..."
    })

    try:
        narrative = await run_narrative_agent(
            question=state["question"],
            sql_query=state["sql_query"],
            data=state["data"],
            columns=state["columns"]
        )
        state["narrative"] = narrative
        add_event(state, SSEEventType.NARRATIVE, "Narrative Agent", {
            "narrative": narrative
        })
    except Exception as e:
        state["narrative"] = "Unable to generate insights."
        add_event(state, SSEEventType.ERROR, "Narrative Agent", {"error": str(e)})

    # Final completion event
    add_event(state, SSEEventType.COMPLETE, "System", {
        "message": "Dashboard panel ready!"
    })

    return state


# ── Build the Graph ─────────────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """Build the LangGraph state graph for the agent pipeline."""

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("query_agent", query_node)
    graph.add_node("validator_agent", validator_node)
    graph.add_node("viz_agent", viz_node)
    graph.add_node("narrative_agent", narrative_node)

    # Set entry point
    graph.set_entry_point("query_agent")

    # Add edges
    graph.add_edge("query_agent", "validator_agent")

    # Conditional edge: retry or continue
    graph.add_conditional_edges(
        "validator_agent",
        should_retry,
        {
            "retry": "query_agent",     # Self-correction loop
            "continue": "viz_agent",     # SQL is valid, proceed
            "end": END                   # Error, stop
        }
    )

    graph.add_edge("viz_agent", "narrative_agent")
    graph.add_edge("narrative_agent", END)

    return graph.compile()


# Global compiled graph
agent_graph = build_agent_graph()


async def run_pipeline(question: str):
    """
    Run the full agent pipeline and yield SSE events.
    This is a generator that yields events as they're produced.
    """
    # Get schema context via RAG
    schema_context = schema_rag.query(question)

    # Initial state
    initial_state: AgentState = {
        "question": question,
        "schema_context": schema_context,
        "sql_query": "",
        "sql_error": "",
        "retry_count": 0,
        "max_retries": 3,
        "data": [],
        "columns": [],
        "chart_config": None,
        "narrative": "",
        "error": None,
        "events": []
    }

    # Run the graph
    final_state = await agent_graph.ainvoke(initial_state)

    # Yield all events
    for event in final_state["events"]:
        yield event

    # If there was an error, yield an error event
    if final_state.get("error"):
        yield {
            "event": SSEEventType.ERROR.value,
            "agent": "System",
            "data": {"error": final_state["error"]}
        }

    # Yield final panel data
    panel = DashboardPanel(
        id=str(uuid.uuid4()),
        question=question,
        sql_query=final_state.get("sql_query", ""),
        chart_config=ChartConfig(**final_state["chart_config"]) if final_state.get("chart_config") else None,
        narrative=final_state.get("narrative", ""),
        error=final_state.get("error")
    )

    yield {
        "event": "panel_data",
        "agent": "System",
        "data": panel.model_dump()
    }
