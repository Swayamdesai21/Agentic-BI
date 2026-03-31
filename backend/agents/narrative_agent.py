"""
Narrative Agent: Generates plain-English insight summaries from query results.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os


def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.3,
        max_tokens=512,
    )


NARRATIVE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a business intelligence analyst. Generate a concise, insightful narrative
summary of the data results. Your summary should be professional and actionable.

RULES:
1. Start with the key finding (1 sentence).
2. Highlight 2-3 specific data points or trends.
3. End with a brief actionable insight or observation.
4. Use actual numbers from the data.
5. Keep it under 100 words.
6. Use markdown formatting: **bold** for key metrics, bullet points for findings.
7. Do NOT include SQL or technical details."""),
    ("human", """Question: {question}

SQL Query: {sql_query}

Results ({row_count} rows):
{data_summary}""")
])


async def run_narrative_agent(question: str, sql_query: str, data: list[dict], columns: list[str]) -> str:
    """Generate plain-English insight summary."""

    if not data:
        return "**No data found** for this query. Try adjusting your question or time range."

    # Prepare data summary (limit to prevent token overflow)
    summary_data = data[:20]
    data_str = json.dumps(summary_data, indent=2, default=str)

    if len(data) > 20:
        data_str += f"\n... and {len(data) - 20} more rows"

    llm = get_llm()
    chain = NARRATIVE_PROMPT | llm | StrOutputParser()

    try:
        result = await chain.ainvoke({
            "question": question,
            "sql_query": sql_query,
            "row_count": len(data),
            "data_summary": data_str
        })
        return result.strip()

    except Exception as e:
        # Fallback narrative
        return _fallback_narrative(data, columns)


def _fallback_narrative(data: list[dict], columns: list[str]) -> str:
    """Generate a basic narrative when LLM fails."""
    if not data or not columns:
        return "Query completed but no insights could be generated."

    row_count = len(data)
    col_count = len(columns)

    parts = [f"**{row_count} results** found across {col_count} metrics."]

    # Try to find numeric columns for basic stats
    for col in columns:
        values = [row.get(col) for row in data if isinstance(row.get(col), (int, float))]
        if values:
            total = sum(values)
            avg = total / len(values)
            parts.append(f"- **{col.replace('_', ' ').title()}**: Total = {total:,.2f}, Avg = {avg:,.2f}")
            break

    return "\n".join(parts)
