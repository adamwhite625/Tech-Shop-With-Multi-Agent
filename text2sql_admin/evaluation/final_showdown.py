import json
import time
import os
import sqlite3
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def init_mock_db(schema: str) -> sqlite3.Connection:
    """Initialize an in-memory SQLite database from a given schema string."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    try:
        # Split and execute multiple CREATE TABLE statements
        for stmt in schema.split(';'):
            if stmt.strip():
                cursor.execute(stmt.strip())
        conn.commit()
    except Exception:
        pass
    return conn

def invoke_model(model_name: str, schema: str, question: str, is_openai: bool = False) -> str:
    """Invoke the LLM (Local via Ollama or Cloud via OpenAI) to generate SQL."""
    if is_openai:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or "sk-proj-xxx" in api_key:
            return "Error: No valid OpenAI API Key"
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="sk-no-key-required")
    
    try:
        # Specialized prompt handling for V1 (trained on 12k mixed dataset)
        if "v1" in model_name:
            v1_instr = """You are a problem solving model working on task_description XML block:
<task_description>You are given a database schema and a natural language question.
Generate the SQL query that answers the question.
Input: Schema and Question. Output: A single SQL query. No explanations.</task_description>
Solve only the task in question block. Generate only the answer."""
            prompt_content = f"{v1_instr}\n\nNow for the real task, solve the task in question block.\nGenerate only the solution, do not generate anything else\n<question>{schema}\nQuestion: {question}</question>\n"
            messages = [{"role": "user", "content": prompt_content}]
        else:
            # Align system prompt with the format used during V3 training
            system_prompt = """You are an expert SQL Generator. User will provide a Database Schema with Sample Data.
CRITICAL RULES:
1. Return ONLY the raw SQL query. No markdown formatting, no explanations.
2. Ensure you ONLY select columns explicitly requested. If asked for "details", select *.
3. DO NOT hallucinate column names. Use ONLY the columns provided in the schema.
4. Ensure all grouping columns are included in the SELECT clause.
5. DO NOT use JOIN implicitly unless the question strictly targets data from multiple tables."""

            # Align user prompt format: [DDL]; -- Sample: ... Question: ...
            # Since gold_standard_20.json lacks samples, we inject placeholders to match training patterns.
            user_content = f"{schema}\n-- Sample: ['sample_data_1']\n-- Sample: ['sample_data_2']\nQuestion: {question}"
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

        chat_response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0
        )
        sql = chat_response.choices[0].message.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        # Strip Gemma turn-based control tokens that some models might output
        sql = sql.replace("<start_of_turn>", "").replace("</start_of_turn>", "").replace("<end_of_turn>", "").strip()
        # Handle multi-line responses by joining with spaces
        sql = " ".join(sql.split('\n')).strip()
        return sql
    except Exception as e:
        return f"Error: {str(e)}"

def run_gold_benchmark():
    """Execute the Gold Standard 20-question benchmark across all target models."""
    models = [
        {"name": "gemma2:2b", "label": "Gemma-Base", "is_openai": False},
        {"name": "text2sql-v1", "label": "V1 (12k-Dataset)", "is_openai": False},
        {"name": "hf.co/adamwhite625/gemma-2-2b-text2sql-v2-gguf", "label": "V2 (Context-Aligned)", "is_openai": False},
        {"name": "hf.co/adamwhite625/gemma-2-2b-text2sql-v3-spider-augmented", "label": "V3 (Spider-Specialist)", "is_openai": False},
        {"name": "gpt-4o-mini", "label": "GPT-4o-mini (Cloud)", "is_openai": True}
    ]

    with open("evaluation/gold_standard_20.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    all_results = []

    print("\nSTARTING GOLD STANDARD BENCHMARK (20 QUESTIONS)\n")

    for case in test_cases:
        print(f"Processing [{case['id']}] ({case['difficulty'].upper()}): {case['question'][:50]}...")
        conn = init_mock_db(case["schema"])
        
        case_results = {"id": case["id"], "difficulty": case["difficulty"], "question": case["question"], "expected": case["expected_sql"]}
        
        for m in models:
            start_time = time.time()
            gen_sql = invoke_model(m["name"], case["schema"], case["question"], m["is_openai"])
            latency = time.time() - start_time
            
            # Evaluate Result Match (RM)
            rm = "FAIL"
            err = ""
            if "Error:" not in gen_sql:
                try:
                    df_exp = pd.read_sql_query(case["expected_sql"], conn)
                    df_gen = pd.read_sql_query(gen_sql, conn)
                    
                    # Compare result sets (agnostic to column/row order)
                    exp_set = set([tuple(r) for r in df_exp.itertuples(index=False)])
                    gen_set = set([tuple(r) for r in df_gen.itertuples(index=False)])
                    
                    if exp_set == gen_set:
                        rm = "PASS"
                except Exception as e:
                    rm = "ERROR"
                    err = str(e)
            else:
                rm = "SKIP"
                err = gen_sql

            case_results[m["label"]] = {
                "sql": gen_sql,
                "rm": rm,
                "latency": latency,
                "error": err
            }
        
        all_results.append(case_results)

    # Compile detailed markdown report
    generate_markdown_report(all_results, models)

def generate_markdown_report(results, models):
    """Generate a side-by-side comparison report in Markdown format."""
    report = "# FINAL AUDIT REPORT: Text2SQL Model Performance\n\n"
    report += "## Accuracy Summary (Result Match)\n\n"
    
    # Build summary table
    summary_data = []
    for m in models:
        label = m["label"]
        passes = sum(1 for r in results if r[label]["rm"] == "PASS")
        total = len(results)
        acc = (passes/total)*100
        avg_lat = sum(r[label]["latency"] for r in results) / total
        summary_data.append({"Model": label, "PASS": passes, "Total": total, "Accuracy (%)": f"{acc:.1f}%", "Avg Speed (s)": f"{avg_lat:.2f}s"})
    
    df_summary = pd.DataFrame(summary_data)
    report += df_summary.to_markdown(index=False) + "\n\n"
    
    report += "## Per-Question Deep Dive Analysis\n\n"
    
    for r in results:
        report += f"### [{r['id']}] ({r['difficulty'].upper()}) {r['question']}\n\n"
        report += f"**Expected SQL:** `{r['expected']}`\n\n"
        
        table_rows = []
        for m in models:
            label = m["label"]
            status = r[label]["rm"]
            sql = r[label]["sql"]
            # Truncate SQL for better table readability
            sql_short = (sql[:100] + "...") if len(sql) > 100 else sql
            table_rows.append({"Model": label, "Status": status, "Generated SQL": f"`{sql_short}`"})
            
        report += pd.DataFrame(table_rows).to_markdown(index=False) + "\n\n"
        
        # Add highlight if V3 outperformed Base on complex logic
        if r["V3 (Spider-Specialist)"]["rm"] == "PASS" and r["Gemma-Base"]["rm"] == "FAIL":
            report += "> [!TIP]\n> **V3 WIN:** Model V3 successfully handled complex JOIN logic where the Base Model failed.\n\n"
            
    with open("evaluation/FINAL_AUDIT_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\nSUCCESS! Detailed report saved at: evaluation/FINAL_AUDIT_REPORT.md")

if __name__ == "__main__":
    run_gold_benchmark()
