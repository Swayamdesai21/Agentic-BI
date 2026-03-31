"""
Query Agent: Converts natural language questions into SQL using Groq LLM + RAG context.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import re


def get_llm():
    """Get configured Groq LLM instance."""
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=2048,
    )


QUERY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert SQL query generator for a SQLite database.
Your job is to convert natural language questions into valid SQLite SQL queries.

DATABASE SCHEMA AND CONTEXT:
{schema_context}

RULES:
1. Generate ONLY the SQL query, nothing else. No explanations, no markdown.
2. Use SQLite syntax (strftime for dates, || for string concat).
3. Always include appropriate WHERE clauses to filter data meaningfully.
4. Use aliases for readability (e.g., AS revenue, AS month).
5. For date grouping, use strftime('%Y-%m', order_date) for monthly, strftime('%Y-%W', order_date) for weekly.
6. Always ORDER BY the most logical column.
7. For "top N" questions, use LIMIT.
8. Exclude cancelled orders unless specifically asked about them (WHERE status != 'cancelled' or WHERE status = 'completed').
9. ROUND numeric results to 2 decimal places.
10. If the question is ambiguous, make a reasonable assumption and generate the query.

{error_context}"""),
    ("human", "{question}")
])


def extract_sql(text: str) -> str:
    """Extract clean SQL from LLM response."""
    # Remove markdown code blocks if present
    text = text.strip()
    sql_match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL)
    if sql_match:
        text = sql_match.group(1)
    else:
        sql_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if sql_match:
            text = sql_match.group(1)

    # Remove any non-SQL text
    text = text.strip()
    # Ensure it starts with a SQL keyword
    sql_keywords = ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
    for keyword in sql_keywords:
        if text.upper().startswith(keyword):
            return text

    # Try to find SQL within the text
    for keyword in sql_keywords:
        idx = text.upper().find(keyword)
        if idx != -1:
            return text[idx:]

    return text


async def run_query_agent(question: str, schema_context: str, error_context: str = "") -> str:
    """Generate SQL from natural language question."""
    llm = get_llm()
    chain = QUERY_PROMPT | llm | StrOutputParser()

    result = await chain.ainvoke({
        "question": question,
        "schema_context": schema_context,
        "error_context": error_context
    })

    return extract_sql(result)
