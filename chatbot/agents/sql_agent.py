import json
import logging
import re
import psycopg2
import requests
from urllib.parse import urlparse
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Keywords that must never appear in LLM-generated SQL
_DANGEROUS_SQL_KEYWORDS = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REPLACE|MERGE|EXEC|EXECUTE|GRANT|REVOKE|COPY|CALL)\b',
    re.IGNORECASE,
)

# Allowed LLM API hostnames (add more as needed via env or config)
_ALLOWED_LLM_HOSTS = {
    "openrouter.ai",
    "api.openai.com",
    "api.anthropic.com",
    "openai.azure.com",
}


def _validate_sql(sql: str) -> None:
    """Raise ValueError if sql is not a safe SELECT-only statement."""
    clean = sql.strip().lstrip(";").strip()
    if not clean.upper().startswith("SELECT"):
        raise ValueError("Only SELECT statements are permitted.")
    match = _DANGEROUS_SQL_KEYWORDS.search(clean)
    if match:
        raise ValueError(f"Forbidden SQL keyword detected: {match.group()}")


def _validate_endpoint(endpoint: str) -> None:
    """Raise ValueError if endpoint points to a disallowed host."""
    parsed = urlparse(endpoint)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("LLM endpoint must use http or https.")
    host = (parsed.hostname or "").lower()
    if not any(host == allowed or host.endswith(f".{allowed}") for allowed in _ALLOWED_LLM_HOSTS):
        raise ValueError(f"LLM endpoint host '{host}' is not in the allowed list.")


def _get_schema() -> str:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            rows = cur.fetchall()

    schema: dict = {}
    for table, col, dtype in rows:
        schema.setdefault(table, []).append(f"{col} ({dtype})")

    lines = []
    for table, cols in schema.items():
        lines.append(f"Table: {table}")
        for c in cols:
            lines.append(f"  - {c}")
    return "\n".join(lines)


def _execute_sql(sql: str) -> list:
    _validate_sql(sql)
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _call_llm(messages: list, model_config: dict) -> str:
    endpoint = model_config.get("endpoint", "")
    _validate_endpoint(endpoint)
    resp = requests.post(
        f"{endpoint}/chat/completions",
        headers={"Authorization": f"Bearer {model_config['apikey']}",
                 "Content-Type": "application/json"},
        json={"model": model_config["modelcode"], "messages": messages, "max_tokens": 1000},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def run(question: str, model_config: dict, history: list = None) -> dict:
    schema = _get_schema()

    sql_messages = [
        {"role": "system", "content": (
            f"You are a PostgreSQL expert. Convert natural language to SQL.\n\n"
            f"Schema:\n{schema}\n\n"
            "Rules: SELECT only, LIMIT 100, return raw SQL with no markdown."
        )},
        *((history or [])[-4:]),
        {"role": "user", "content": question},
    ]

    raw_sql = _call_llm(sql_messages, model_config).strip()

    # Strip markdown code fences if model adds them
    if "```" in raw_sql:
        raw_sql = raw_sql.split("```")[1]
        if raw_sql.startswith("sql"):
            raw_sql = raw_sql[3:]
    sql = raw_sql.strip()

    logger.info("SQL Agent query: %s", sql)

    try:
        data = _execute_sql(sql)
        summary = _call_llm([
            {"role": "system", "content": "Summarize this database result as a clear, concise answer."},
            {"role": "user",   "content": f"Question: {question}\nSQL: {sql}\nResult: {json.dumps(data[:10], default=str)}"},
        ], model_config)
        return {"answer": summary, "sql": sql, "data": data}
    except Exception as e:
        logger.error("SQL execution error: %s", e)
        return {"answer": f"Could not retrieve data: {str(e)}", "sql": sql, "data": []}
