#!/usr/bin/env python3
import argparse
import sqlite3
import sys
from pathlib import Path
import pandas as pd
from model_client import DistilLabsLLM

def load_csv_to_sqlite(csv_paths: list[str], conn: sqlite3.Connection) -> dict[str, str]:
    """Load multiple CSV files into an in-memory SQLite database and return their schemas."""
    schemas = {}
    for csv_path in csv_paths:
        path = Path(csv_path)
        table_name = path.stem.replace("-", "_").replace(" ", "_").lower()
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, index=False, if_exists="replace")

        columns = []
        for col in df.columns:
            dtype = df[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                sql_type = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                sql_type = "REAL"
            else:
                sql_type = "TEXT"
            columns.append(f"  {col} {sql_type}")

        create_stmt = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"
        schemas[table_name] = create_stmt
    return schemas

def format_question(schema: str, question: str) -> str:
    """Format the database schema and natural language question into a prompt."""
    return f"""Schema:\n{schema}\n\nQuestion: {question}"""

def execute_query(conn: sqlite3.Connection, sql: str) -> pd.DataFrame:
    """Execute a SQL query against the SQLite connection and return results as a DataFrame."""
    return pd.read_sql_query(sql, conn)

def main():
    """Main entry point for the CLI tool to query CSV data."""
    parser = argparse.ArgumentParser(description="Text2SQL: Query CSV data using natural language")
    parser.add_argument("--csv", type=str, action="append", required=True)
    parser.add_argument("--question", type=str, required=True)
    parser.add_argument("--model", type=str, default="text2sql-12k")
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--api-key", type=str, default="EMPTY")
    parser.add_argument("--show-sql", action="store_true")

    args = parser.parse_args()

    for csv_path in args.csv:
        if not Path(csv_path).exists():
            print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
            sys.exit(1)

    conn = sqlite3.connect(":memory:")

    try:
        schemas = load_csv_to_sqlite(args.csv, conn)
    except Exception as e:
        print(f"Error loading CSV files: {e}", file=sys.stderr)
        sys.exit(1)

    full_schema = "\n\n".join(schemas.values())

    client = DistilLabsLLM(model_name=args.model, api_key=args.api_key, port=args.port)
    formatted_input = format_question(full_schema, args.question)

    try:
        sql = client.invoke(formatted_input).strip()
        sql = sql.split("</")[0].strip()
    except Exception as e:
        print(f"Error generating SQL: {e}", file=sys.stderr)
        sys.exit(1)

    if args.show_sql:
        print(f"Generated SQL: {sql}\n")

    try:
        results = execute_query(conn, sql)
        print(results.to_string(index=False))
    except Exception as e:
        print(f"Error executing query: {e}", file=sys.stderr)
        print(f"Generated SQL was: {sql}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()