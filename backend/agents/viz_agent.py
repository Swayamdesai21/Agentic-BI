"""
Visualization Agent: Selects chart type and generates Pydantic-validated config.
Analyzes query results shape to pick the optimal chart type.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from models import ChartConfig, ChartType
import json
import os
import re


def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=1024,
    )


VIZ_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data visualization expert. Given a user's question and query results,
select the best chart type and generate a chart configuration.

RULES:
1. Choose the chart type based on the data shape:
   - Time series data (dates/months) → "line" or "area"
   - Categorical comparisons (products, categories, regions) → "bar"
   - Part-of-whole / proportions → "pie" (only if ≤ 8 categories)
   - Raw tabular data with many columns → "table"

2. Return ONLY valid JSON matching this schema:
{{
    "chart_type": "bar" | "line" | "pie" | "area" | "table",
    "title": "Descriptive chart title",
    "x_key": "column_name_for_x_axis",
    "y_key": "column_name_for_y_axis",
    "x_label": "Human readable X axis label",
    "y_label": "Human readable Y axis label"
}}

3. x_key and y_key MUST match actual column names from the data.
4. For pie charts, x_key = label column, y_key = value column.
5. Generate a concise, descriptive title.
6. Return ONLY the JSON object, no explanations."""),
    ("human", """Question: {question}

Column names: {columns}

Sample data (first 5 rows):
{sample_data}

Total rows: {row_count}""")
])


COLOR_PALETTES = {
    "bar": ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#818cf8", "#6d28d9"],
    "line": ["#14b8a6", "#2dd4bf", "#5eead4", "#99f6e4", "#0d9488", "#0f766e"],
    "area": ["#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe", "#e0e7ff", "#4f46e5"],
    "pie": ["#6366f1", "#f59e0b", "#14b8a6", "#f43f5e", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316"],
    "table": ["#6366f1"],
}


async def run_viz_agent(question: str, data: list[dict], columns: list[str]) -> ChartConfig:
    """Generate chart configuration from query results."""

    if not data or not columns:
        return ChartConfig(
            chart_type=ChartType.TABLE,
            title="No Data Available",
            data=[]
        )

    # Prepare context
    sample = data[:5]
    sample_str = json.dumps(sample, indent=2, default=str)

    llm = get_llm()
    chain = VIZ_PROMPT | llm | StrOutputParser()

    try:
        result = await chain.ainvoke({
            "question": question,
            "columns": ", ".join(columns),
            "sample_data": sample_str,
            "row_count": len(data)
        })

        # Parse JSON from response
        result = result.strip()
        # Extract JSON if wrapped in markdown
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)

        config_dict = json.loads(result)

        # Validate chart_type
        chart_type = config_dict.get("chart_type", "bar")
        if chart_type not in [ct.value for ct in ChartType]:
            chart_type = "bar"

        # Build chart config with data
        chart_config = ChartConfig(
            chart_type=ChartType(chart_type),
            title=config_dict.get("title", "Query Results"),
            x_key=config_dict.get("x_key", columns[0] if columns else ""),
            y_key=config_dict.get("y_key", columns[1] if len(columns) > 1 else columns[0]),
            data=data,
            colors=COLOR_PALETTES.get(chart_type, COLOR_PALETTES["bar"]),
            x_label=config_dict.get("x_label", ""),
            y_label=config_dict.get("y_label", "")
        )

        return chart_config

    except Exception as e:
        print(f"Viz agent error: {e}, using fallback")
        # Fallback: auto-detect chart type
        return _fallback_chart_config(question, data, columns)


def _fallback_chart_config(question: str, data: list[dict], columns: list[str]) -> ChartConfig:
    """Fallback chart configuration when LLM fails."""
    if len(columns) < 2:
        return ChartConfig(
            chart_type=ChartType.TABLE,
            title="Query Results",
            data=data,
            x_key=columns[0] if columns else "",
            y_key=columns[0] if columns else ""
        )

    # Detect chart type from data shape
    chart_type = ChartType.BAR
    x_key = columns[0]
    y_key = columns[1]

    # Check if first column looks like dates
    first_val = str(data[0].get(columns[0], ""))
    if any(date_hint in first_val for date_hint in ["-", "/"]) and len(first_val) >= 7:
        chart_type = ChartType.LINE

    # Check if small number of categories → pie
    if len(data) <= 6 and len(columns) == 2:
        chart_type = ChartType.PIE

    return ChartConfig(
        chart_type=chart_type,
        title="Query Results",
        x_key=x_key,
        y_key=y_key,
        data=data,
        colors=COLOR_PALETTES.get(chart_type.value, COLOR_PALETTES["bar"]),
        x_label=x_key.replace("_", " ").title(),
        y_label=y_key.replace("_", " ").title()
    )
