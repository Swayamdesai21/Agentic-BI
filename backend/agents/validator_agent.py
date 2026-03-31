"""
Validator Agent: Validates SQL queries and provides error feedback for self-correction.
"""

from database import validate_sql, execute_query


async def run_validator_agent(sql: str) -> dict:
    """
    Validate and test-execute a SQL query.

    Returns:
        dict with keys:
            - valid: bool
            - error: str (error message if invalid)
            - data: list[dict] (results if valid)
            - columns: list[str] (column names if valid)
    """
    # Step 1: Syntax validation
    is_valid, message = validate_sql(sql)
    if not is_valid:
        return {
            "valid": False,
            "error": f"SQL Syntax Error: {message}",
            "data": [],
            "columns": []
        }

    # Step 2: Execute and check for runtime errors
    try:
        data, columns = execute_query(sql)

        # Step 3: Sanity checks
        if not data:
            return {
                "valid": True,
                "error": "",
                "data": [],
                "columns": columns,
                "warning": "Query returned no results. The query may be too restrictive."
            }

        if len(data) > 1000:
            return {
                "valid": True,
                "error": "",
                "data": data[:100],  # Truncate for safety
                "columns": columns,
                "warning": f"Query returned {len(data)} rows, truncated to 100."
            }

        return {
            "valid": True,
            "error": "",
            "data": data,
            "columns": columns
        }

    except Exception as e:
        return {
            "valid": False,
            "error": f"SQL Runtime Error: {str(e)}",
            "data": [],
            "columns": []
        }
