import json
import re
import random

def extract_tables_and_columns(ddl_string: str) -> list[dict]:
    """Extract table names and column lists from a given CREATE TABLE DDL string."""
    tables = []
    # Simple parsing: CREATE TABLE table_name (col type, ...)
    for match in re.finditer(r"CREATE TABLE\s+([a-zA-Z0-9_]+)\s*\((.*?)\)", ddl_string, re.IGNORECASE):
        table_name = match.group(1)
        cols_str = match.group(2)
        columns = []
        for col_def in cols_str.split(','):
            parts = col_def.strip().split()
            if parts:
                columns.append(parts[0])
        tables.append({"name": table_name, "columns": columns, "full_stmt": match.group(0)})
    return tables

def generate_mock_row(columns: list[str]) -> str:
    """Generate mock sample data rows based on column name heuristics (id, date, amount, etc.)."""
    row = []
    for col in columns:
        col_lower = col.lower()
        if "id" in col_lower:
            row.append(str(random.randint(1, 1000)))
        elif "date" in col_lower or "time" in col_lower or "year" in col_lower:
            row.append("'2023-01-01'")
        elif "amount" in col_lower or "budget" in col_lower or "salary" in col_lower:
            row.append(str(round(random.uniform(1000, 90000), 2)))
        elif "age" in col_lower:
            row.append(str(random.randint(18, 65)))
        else:
            row.append(f"'sample_{col}'")
    return "[" + ", ".join(row) + "]"

def process_huggingface():
    """Download, filter, and augment the b-mc2/sql-create-context dataset for V3 training."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: 'datasets' library not found.")
        print("Please run: pip install datasets")
        return
        
    print("Downloading b-mc2/sql-create-context dataset (78k queries)...")
    dataset = load_dataset("b-mc2/sql-create-context", split="train")
    
    # Golden system prompt used for V3 fine-tuning
    system_prompt = """You are an expert SQL Generator. User will provide a Database Schema with Sample Data.
CRITICAL RULES:
1. Return ONLY the raw SQL query. No markdown formatting, no explanations.
2. Ensure you ONLY select columns explicitly requested. If asked for "details", select *.
3. DO NOT hallucinate column names. Use ONLY the columns provided in the schema.
4. Ensure all grouping columns are included in the SELECT clause.
5. DO NOT use JOIN implicitly unless the question strictly targets data from multiple tables."""
    
    processed_count = 0
    complex_count = 0
    output_data = []
    
    print("Filtering hard queries (JOIN, GROUP BY) and injecting Mock Data...")
    
    # Sample ~8000 records, prioritizing complex queries for V3 specialization.
    for row in dataset:
        sql = row["answer"]
        is_complex = any(keyword in sql.upper() for keyword in ["JOIN", "GROUP BY", "HAVING", "INTERSECT", "EXCEPT", "UNION"])
        
        # Keep only 5% of simple queries to prevent over-specialization while focusing on complexity.
        if not is_complex and random.random() > 0.05:
            continue
            
        if is_complex:
            complex_count += 1
            
        context = row["context"]
        tables = extract_tables_and_columns(context)
        
        augmented_context = ""
        for tbl in tables:
            augmented_context += tbl["full_stmt"] + ";\n"
            # Inject 2 rows of mock Sample Data to mimic the target environment
            augmented_context += f"-- Sample: {generate_mock_row(tbl['columns'])}\n"
            augmented_context += f"-- Sample: {generate_mock_row(tbl['columns'])}\n"
            
        user_content = f"{augmented_context}\nQuestion: {row['question']}"
        
        record = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": sql}
            ]
        }
        output_data.append(record)
        processed_count += 1
        
        if processed_count >= 8000:
            break
            
    random.shuffle(output_data)
    
    out_file = "data_pipeline/spider_augmented_v3.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for r in output_data:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"DONE! Saved {processed_count} records (including {complex_count} complex queries) to {out_file}")
    print("Ready for V3 fine-tuning.")

if __name__ == "__main__":
    process_huggingface()
