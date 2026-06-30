#!/usr/bin/env python3
"""FastAPI backend for Text2SQL Admin — supports MySQL (primary) and CSV upload (secondary)."""

import os
import re
import sqlite3
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

import pandas as pd
import pymysql
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from model_client import DistilLabsLLM

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
MODEL_NAME = os.getenv("MODEL_NAME", "hf.co/adamwhite625/gemma-2-2b-text2sql-v3-spider-augmented")
API_KEY = os.getenv("API_KEY", "EMPTY")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))

# MySQL config — connects to the Tech Shop database
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "tech_store_db")

# SQL keywords that are forbidden in generated queries
DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "TRUNCATE", "CREATE", "REPLACE", "GRANT", "REVOKE",
]

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
csv_db_conn: sqlite3.Connection | None = None
csv_table_schemas: dict[str, str] = {}
mysql_table_schemas: dict[str, str] = {}
llm_client: DistilLabsLLM | None = None


# ---------------------------------------------------------------------------
# MySQL helpers
# ---------------------------------------------------------------------------
def get_mysql_connection() -> pymysql.Connection:
    """Open a new MySQL connection to the Tech Shop database."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
    )


def load_mysql_schemas() -> dict[str, str]:
    """Read CREATE TABLE DDL for every table in the MySQL database."""
    schemas = {}
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"SHOW CREATE TABLE `{table}`")
            row = cursor.fetchone()
            ddl = row.get("Create Table", "")

            # Fetch 3 sample rows to enrich context for the LLM
            try:
                cursor.execute(f"SELECT * FROM `{table}` LIMIT 3")
                sample_rows = cursor.fetchall()
                if sample_rows:
                    for sr in sample_rows:
                        vals = []
                        for v in sr.values():
                            if v is None:
                                vals.append("NULL")
                            elif isinstance(v, str):
                                clean = v.replace("'", "''").replace("\n", " ")[:80]
                                vals.append(f"'{clean}'")
                            else:
                                vals.append(str(v))
                        ddl += f"\n-- Sample: INSERT INTO {table} VALUES ({', '.join(vals)});"
            except Exception:
                pass

            schemas[table] = ddl
        conn.close()
    except Exception as e:
        print(f"[WARNING] Failed to load MySQL schemas: {e}")
    return schemas


def get_mysql_table_row_count(table_name: str) -> int:
    """Return the row count for a single MySQL table."""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{table_name}`")
        result = cursor.fetchone()
        conn.close()
        return result["cnt"] if result else 0
    except Exception:
        return 0


def execute_query_mysql(sql: str) -> pd.DataFrame:
    """Execute a read-only SQL query against the MySQL database."""
    conn = get_mysql_connection()
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# SQL safety layer
# ---------------------------------------------------------------------------
def validate_sql_safety(sql: str) -> bool:
    """Only allow SELECT statements. Block any write or DDL operations."""
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        return False
    for keyword in DANGEROUS_KEYWORDS:
        # Match keyword as whole word to avoid false positives (e.g. "UPDATED_AT")
        if re.search(rf'\b{keyword}\b', normalized):
            return False
    return True


# ---------------------------------------------------------------------------
# CSV / SQLite helpers (secondary feature, kept from original)
# ---------------------------------------------------------------------------
def load_csv_to_sqlite(csv_path: str, conn: sqlite3.Connection) -> tuple[str, str, list[dict], int]:
    """Load a CSV file into the in-memory SQLite DB. Returns (table_name, DDL, columns, row_count)."""
    path = Path(csv_path)
    table_name = path.stem.replace("-", "_").replace(" ", "_").lower()
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, conn, index=False, if_exists="replace")

    columns = []
    col_info = []
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            sql_type = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            sql_type = "REAL"
        else:
            sql_type = "TEXT"
        columns.append(f"  {col} {sql_type}")
        col_info.append({"name": col, "type": sql_type})

    create_stmt = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"

    # Add sample rows as comments for LLM context
    if not df.empty:
        for _, row in df.head(3).iterrows():
            vals = []
            for v in row.values:
                if pd.isna(v):
                    vals.append("NULL")
                elif isinstance(v, str):
                    clean_str = v.replace("'", "''").replace("\n", " ")
                    vals.append(f"'{clean_str}'")
                else:
                    vals.append(str(v))
            create_stmt += f"\n-- Sample: INSERT INTO {table_name} VALUES ({', '.join(vals)});"

    return table_name, create_stmt, col_info, len(df)


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------
def format_question(schema: str, question: str) -> str:
    """Build a structured prompt with schema context and few-shot examples."""
    return (
        "Instructions:\n"
        "1. You are a Text2SQL engine. Output ONLY raw SQL for MySQL.\n"
        "2. For comparisons with averages, always use a subquery in the WHERE clause.\n"
        "3. Use backticks for reserved words and table/column names when needed.\n\n"
        "Example 1:\n"
        "Question: List projects with a budget higher than the average.\n"
        "SQL: SELECT name FROM projects WHERE budget > (SELECT AVG(budget) FROM projects)\n\n"
        "Example 2:\n"
        "Question: Show employees earning more than the average salary.\n"
        "SQL: SELECT name FROM employees WHERE salary > (SELECT AVG(salary) FROM employees)\n\n"
        "Current Task:\n"
        f"Schema:\n{schema}\n\n"
        f"Question: {question}\n\n"
        "Critical Rules:\n"
        "- NEVER put 'HAVING' inside the 'SELECT' clause.\n"
        "- Do not include markdown formatting or explanations.\n"
        "- Output ONLY a SELECT query. Never output INSERT, UPDATE, DELETE, or DROP.\n"
        "SQL:"
    )


def fix_missing_group_by_columns(sql: str) -> str:
    """If SQL has GROUP BY col but col is not in SELECT, inject it to prevent data loss."""
    group_by_match = re.search(r'GROUP BY\s+(.+?)(?:\s+(?:ORDER BY|LIMIT|HAVING)|$)', sql, re.IGNORECASE)
    if not group_by_match:
        return sql

    group_cols_str = group_by_match.group(1)
    group_cols = [c.strip() for c in group_cols_str.split(",")]

    select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE)
    if not select_match:
        return sql

    select_content = select_match.group(1)

    missing_cols = []
    for col in group_cols:
        col_clean = col.split(".")[-1].strip("`")
        if col_clean not in select_content and col not in select_content:
            missing_cols.append(col)

    if missing_cols:
        new_select = f"SELECT {', '.join(missing_cols)}, {select_content} FROM"
        sql = re.sub(r'SELECT\s+(.+?)\s+FROM', new_select, sql, count=1, flags=re.IGNORECASE)

    return sql


def clean_llm_output(raw: str) -> str:
    """Strip XML tags, markdown fences, and whitespace from raw LLM response."""
    sql = raw.strip()
    sql = sql.split("</")[0].strip()
    if sql.startswith("```"):
        sql = "\n".join(sql.split("\n")[1:])
    if sql.endswith("```"):
        sql = sql[: sql.rfind("```")].strip()
    return sql.strip()


# ---------------------------------------------------------------------------
# Lifespan — init on startup, cleanup on shutdown
# ---------------------------------------------------------------------------
def _init_state():
    """Initialize LLM client, SQLite for CSV uploads, and load MySQL schemas."""
    global csv_db_conn, csv_table_schemas, mysql_table_schemas, llm_client

    if csv_db_conn is not None:
        try:
            csv_db_conn.close()
        except Exception:
            pass

    csv_db_conn = sqlite3.connect(":memory:", check_same_thread=False)
    csv_table_schemas = {}

    llm_client = DistilLabsLLM(
        model_name=MODEL_NAME,
        api_key=API_KEY,
        host=OLLAMA_HOST,
        port=OLLAMA_PORT,
    )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Load MySQL schemas on startup
    mysql_table_schemas = load_mysql_schemas()
    print(f"[INFO] Loaded {len(mysql_table_schemas)} tables from MySQL ({MYSQL_DATABASE})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_state()
    yield
    if csv_db_conn is not None:
        csv_db_conn.close()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Text2SQL Admin API",
    description="Admin dashboard: query Tech Shop database using natural language, or upload CSV for ad-hoc analysis.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    source: str = "mysql"  # "mysql" or "csv"


class QueryResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int
    source: str


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    model_loaded: bool
    model_name: str
    mysql_connected: bool
    mysql_tables: int
    csv_tables: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check Ollama and MySQL connectivity status."""
    health = llm_client.check_health()

    mysql_ok = False
    try:
        conn = get_mysql_connection()
        conn.ping(reconnect=False)
        conn.close()
        mysql_ok = True
    except Exception:
        pass

    return HealthResponse(
        status="ok" if health["ollama"] and mysql_ok else "degraded",
        ollama=health["ollama"],
        model_loaded=health["model_loaded"],
        model_name=health["model_name"],
        mysql_connected=mysql_ok,
        mysql_tables=len(mysql_table_schemas),
        csv_tables=len(csv_table_schemas),
    )


@app.get("/api/tables")
async def list_tables():
    """List all available tables from both MySQL and CSV sources."""
    tables = []

    # MySQL tables (primary)
    for name, ddl in mysql_table_schemas.items():
        row_count = get_mysql_table_row_count(name)
        tables.append({
            "name": name,
            "schema": ddl,
            "row_count": row_count,
            "source": "mysql",
        })

    # CSV tables (secondary)
    for name, ddl in csv_table_schemas.items():
        try:
            count = csv_db_conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        except Exception:
            count = 0
        tables.append({
            "name": name,
            "schema": ddl,
            "row_count": count,
            "source": "csv",
        })

    return {"tables": tables}


@app.post("/api/tables/refresh")
async def refresh_mysql_tables():
    """Reload table schemas from MySQL (useful after schema changes)."""
    global mysql_table_schemas
    mysql_table_schemas = load_mysql_schemas()
    return {"refreshed": len(mysql_table_schemas), "tables": list(mysql_table_schemas.keys())}


@app.post("/api/upload")
async def upload_csv(files: list[UploadFile] = File(...)):
    """Upload CSV files for ad-hoc analysis. Loaded into in-memory SQLite."""
    results = []
    for file in files:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail=f"Not a CSV file: {file.filename}")

        dest = UPLOAD_DIR / file.filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            table_name, ddl, col_info, row_count = load_csv_to_sqlite(str(dest), csv_db_conn)
            csv_table_schemas[table_name] = ddl
            results.append({
                "filename": file.filename,
                "table_name": table_name,
                "schema": ddl,
                "columns": col_info,
                "row_count": row_count,
                "source": "csv",
            })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error loading {file.filename}: {e}")

    return {"uploaded": len(results), "tables": results}


@app.delete("/api/tables/{table_name}")
async def delete_table(table_name: str):
    """Remove a CSV-uploaded table. MySQL tables cannot be deleted from this interface."""
    if table_name in mysql_table_schemas:
        raise HTTPException(
            status_code=403,
            detail=f"Cannot delete MySQL table '{table_name}' from admin interface. Use a database tool instead.",
        )

    if table_name not in csv_table_schemas:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")

    try:
        csv_db_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        del csv_table_schemas[table_name]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"deleted": table_name}


@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Generate SQL from natural language and execute it against MySQL or CSV data."""
    source = req.source.lower()

    # Determine which schemas and executor to use
    if source == "csv":
        if not csv_table_schemas:
            raise HTTPException(status_code=400, detail="No CSV tables loaded. Upload CSV files first.")
        schemas = csv_table_schemas
    else:
        if not mysql_table_schemas:
            raise HTTPException(status_code=400, detail="No MySQL tables available. Check database connection.")
        schemas = mysql_table_schemas

    full_schema = "\n\n".join(schemas.values())
    formatted_input = format_question(full_schema, req.question)

    # Generate SQL via LLM
    try:
        raw_sql = llm_client.invoke(formatted_input)
        sql = clean_llm_output(raw_sql)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    # Safety check: only SELECT allowed
    if not validate_sql_safety(sql):
        raise HTTPException(
            status_code=400,
            detail=f"Safety violation: only SELECT queries are allowed. Generated: {sql}",
        )

    # Auto-fix missing GROUP BY columns
    sql = fix_missing_group_by_columns(sql)

    # Execute against the appropriate backend
    try:
        if source == "csv":
            df = pd.read_sql_query(sql, csv_db_conn)
        else:
            df = execute_query_mysql(sql)

        return QueryResponse(
            sql=sql,
            columns=list(df.columns),
            rows=df.values.tolist(),
            row_count=len(df),
            source=source,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"SQL execution error: {e}\nGenerated SQL: {sql}",
        )


# ---------------------------------------------------------------------------
# Run directly: uvicorn api:app --port 8010 --reload
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8010, reload=True)
