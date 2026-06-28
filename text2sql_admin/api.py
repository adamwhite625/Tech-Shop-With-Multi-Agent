#!/usr/bin/env python3
"""FastAPI backend for Text2SQL Web UI."""

import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model_client import DistilLabsLLM

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
MODEL_NAME = os.getenv("MODEL_NAME", "hf.co/adamwhite625/gemma-2-2b-text2sql-v3-spider-augmented")
API_KEY = os.getenv("API_KEY", "EMPTY")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))

# ---------------------------------------------------------------------------
# State (module-level, reset on restart)
# ---------------------------------------------------------------------------
db_conn: sqlite3.Connection | None = None
table_schemas: dict[str, str] = {}
llm_client: DistilLabsLLM | None = None


def _init_state():
    """Initialize / reset global state."""
    global db_conn, table_schemas, llm_client

    if db_conn is not None:
        try:
            db_conn.close()
        except Exception:
            pass

    db_conn = sqlite3.connect(":memory:", check_same_thread=False)
    table_schemas = {}
    llm_client = DistilLabsLLM(
        model_name=MODEL_NAME,
        api_key=API_KEY,
        host=OLLAMA_HOST,
        port=OLLAMA_PORT,
    )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_state()
    yield
    if db_conn is not None:
        db_conn.close()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Text2SQL API",
    description="Natural-language queries on CSV data powered by a local LLM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int


class TableInfo(BaseModel):
    name: str
    schema_ddl: str
    row_count: int
    columns: list[dict]


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    model_loaded: bool
    model_name: str
    tables_loaded: int


# ---------------------------------------------------------------------------
# Helper functions (reused from app.py logic)
# ---------------------------------------------------------------------------
def load_csv_to_sqlite(csv_path: str, conn: sqlite3.Connection) -> tuple[str, str]:
    """Load a CSV file into SQLite. Returns (table_name, CREATE TABLE DDL)."""
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

    # Add sample data as comments to help the LLM understand the columns
    if not df.empty:
        sample_df = df.head(3)
        sample_rows = []
        for _, row in sample_df.iterrows():
            vals = []
            for v in row.values:
                if pd.isna(v):
                    vals.append("NULL")
                elif isinstance(v, str):
                    # Escape single quotes and avoid multiline breaks
                    clean_str = v.replace("'", "''").replace('\n', ' ')
                    vals.append(f"'{clean_str}'")
                else:
                    vals.append(str(v))
            sample_rows.append(f"-- Sample: INSERT INTO {table_name} VALUES ({', '.join(vals)});")
        create_stmt += "\n" + "\n".join(sample_rows)

    return table_name, create_stmt, col_info, len(df)


def format_question(schema: str, question: str) -> str:
    """Format the schema and question into a structured few-shot prompt."""
    return (
        "Instructions:\n"
        "1. You are a Text2SQL engine. Output ONLY raw SQL for SQLite.\n"
        "2. For comparisons with averages, always use a subquery in the WHERE clause.\n\n"
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
        "SQL:"
    )


def fix_missing_group_by_columns(sql: str) -> str:
    """If SQL has GROUP BY col, but col is not in SELECT, inject it to prevent UI data loss."""
    import re
    # Find GROUP BY ... (until end of string, ORDER BY, or LIMIT)
    group_by_match = re.search(r'GROUP BY\s+(.+?)(?:\s+(?:ORDER BY|LIMIT)|$)', sql, re.IGNORECASE)
    if not group_by_match:
        return sql
        
    group_cols_str = group_by_match.group(1)
    group_cols = [c.strip() for c in group_cols_str.split(',')]
    
    # Find SELECT ... FROM
    select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE)
    if not select_match:
        return sql
        
    select_content = select_match.group(1)
    
    missing_cols = []
    for col in group_cols:
        col_clean = col.split('.')[-1]  # 'employees.department' -> 'department'
        # Simple check if column name exists in SELECT clause
        if col_clean not in select_content and col not in select_content:
            missing_cols.append(col)
            
    if missing_cols:
        # Reconstruct SELECT clause
        new_select = f"SELECT {', '.join(missing_cols)}, {select_content} FROM"
        # Only replace the first instance
        sql = re.sub(r'SELECT\s+(.+?)\s+FROM', new_select, sql, count=1, flags=re.IGNORECASE)
        
    return sql


def execute_query(conn: sqlite3.Connection, sql: str) -> pd.DataFrame:
    """Execute the given SQL query on the SQLite connection and return a DataFrame."""
    return pd.read_sql_query(sql, conn)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check Ollama connectivity and model status."""
    health = llm_client.check_health()
    return HealthResponse(
        status="ok" if health["ollama"] else "degraded",
        ollama=health["ollama"],
        model_loaded=health["model_loaded"],
        model_name=health["model_name"],
        tables_loaded=len(table_schemas),
    )


@app.post("/api/upload")
async def upload_csv(files: list[UploadFile] = File(...)):
    """Upload one or more CSV files. They are loaded into the in-memory SQLite DB."""
    results = []
    for file in files:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail=f"Not a CSV file: {file.filename}")

        # Save to disk temporarily
        dest = UPLOAD_DIR / file.filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            table_name, ddl, col_info, row_count = load_csv_to_sqlite(str(dest), db_conn)
            table_schemas[table_name] = ddl
            results.append(
                {
                    "filename": file.filename,
                    "table_name": table_name,
                    "schema": ddl,
                    "columns": col_info,
                    "row_count": row_count,
                }
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error loading {file.filename}: {e}")

    return {"uploaded": len(results), "tables": results}


@app.get("/api/tables")
async def list_tables():
    """List all loaded tables with their schemas."""
    tables = []
    for name, ddl in table_schemas.items():
        try:
            count = db_conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        except Exception:
            count = 0
        tables.append({"name": name, "schema": ddl, "row_count": count})
    return {"tables": tables}


@app.delete("/api/tables/{table_name}")
async def delete_table(table_name: str):
    """Drop a table from the in-memory database."""
    if table_name not in table_schemas:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")

    try:
        db_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        del table_schemas[table_name]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"deleted": table_name}


@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Generate SQL from a natural-language question and execute it."""
    if not table_schemas:
        raise HTTPException(status_code=400, detail="No tables loaded. Upload CSV files first.")

    full_schema = "\n\n".join(table_schemas.values())
    formatted_input = format_question(full_schema, req.question)

    # Generate SQL
    try:
        sql = llm_client.invoke(formatted_input).strip()
        # Remove any trailing XML tags the model might produce
        sql = sql.split("</")[0].strip()
        # Remove markdown code fences if present
        if sql.startswith("```"):
            sql = "\n".join(sql.split("\n")[1:])
        if sql.endswith("```"):
            sql = sql[: sql.rfind("```")].strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    # Safety check: only allow SELECT statements
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail=f"Model generated a non-SELECT statement. Generated SQL: {sql}",
        )

    # Auto-fix missing GROUP BY columns
    sql = fix_missing_group_by_columns(sql)

    # Execute
    try:
        df = execute_query(db_conn, sql)
        return QueryResponse(
            sql=sql,
            columns=list(df.columns),
            rows=df.values.tolist(),
            row_count=len(df),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"SQL execution error: {e}\nGenerated SQL: {sql}",
        )


# ---------------------------------------------------------------------------
# Run directly: uvicorn api:app --reload
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
