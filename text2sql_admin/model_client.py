import argparse
import httpx
from openai import OpenAI

DEFAULT_QUESTION = """Schema:
CREATE TABLE clinics (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT,
  phone TEXT
);
CREATE TABLE visits (
  id INTEGER PRIMARY KEY,
  clinic_id INTEGER REFERENCES clinics(id),
  patient_name TEXT,
  visit_date DATE,
  diagnosis TEXT
);
Question: How many patient visits per clinic this year?"""


class DistilLabsLLM(object):
    def __init__(
        self,
        model_name: str,
        api_key: str = "EMPTY",
        host: str = "127.0.0.1",
        port: int = 11434,
        timeout: float = 120.0,
    ):
        self.model_name = model_name
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.client = OpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=api_key,
            timeout=timeout,
        )

    def get_prompt(self, question: str) -> list[dict[str, str]]:
        """Construct the appropriate prompt based on the target model's training background."""
        # Restore original training environment for text2sql-12k model
        if "text2sql-12k" in self.model_name:
            import re
            # Remove Sample Data comments (unknown to model during training)
            clean_question = re.sub(r'-- Sample:.*\n', '', question)
            
            # Use exact training prompt structure without system role
            system_prompt = """You are a problem solving model working on task_description XML block:
<task_description>You are given a database schema and a natural language question.
Generate the SQL query that answers the question.
Input: Schema and Question. Output: A single SQL query. No explanations.</task_description>
Solve only the task in question block. Generate only the answer."""
            
            return [
                {
                    "role": "user",
                    "content": f"{system_prompt}\n\nNow for the real task, solve the task in question block.\nGenerate only the solution, do not generate anything else\n<question>{clean_question}</question>\n",
                }
            ]
            
        # Optimized default prompt for Gemma 2 Base and GPT-4o-mini
        return [
            {
                "role": "system",
                "content": """
You are a problem solving model working on task_description XML block:
<task_description>You are given a database schema and a natural language question.
Generate the SQL query that answers the question.

CRITICAL RULES:
1. Output ONLY the raw SQL query. No markdown formatting (```sql), no explanations, no chat.
2. DO NOT JOIN tables unless the question explicitly requires data from multiple tables. If the required columns are in ONE table, query ONLY that table.
3. When using GROUP BY, you MUST include the grouping column in the SELECT list. 
   - Incorrect: SELECT AVG(salary) FROM employees GROUP BY department
   - Correct: SELECT department, AVG(salary) FROM employees GROUP BY department
4. Use uppercase for SQL formatting (SELECT, FROM, WHERE, GROUP BY, ORDER BY).

EXAMPLES:
Schema: CREATE TABLE products (category TEXT, price REAL);
Question: What is the average price by category?
Correct SQL: SELECT category, AVG(price) FROM products GROUP BY category

Schema: CREATE TABLE users (id INTEGER, city TEXT);
Question: How many users are in each city?
Correct SQL: SELECT city, COUNT(*) FROM users GROUP BY city
</task_description>

You will be given a single task in the question XML block.
Solve only the task in question block.
Generate only the solution, do not generate anything else.
""",
            },
            {
                "role": "user",
                "content": f"""
Now for the real task, solve the task in question block.
Generate only the solution, do not generate anything else
<question>{question}</question>
""",
            },
        ]

    def format_question(self, schema: str, question: str) -> str:
        """Combine schema and question into a single input string."""
        return f"Schema:\n{schema}\n\nQuestion: {question}"

    def invoke(self, question: str) -> str:
        """Send a question to the LLM and return the raw response content."""
        chat_response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.get_prompt(question),
            temperature=0,
        )
        return chat_response.choices[0].message.content

    def check_health(self) -> dict:
        """Check if Ollama server is reachable and model is loaded."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            model_loaded = any(self.model_name in name for name in model_names)
            return {
                "ollama": True,
                "model_loaded": model_loaded,
                "model_name": self.model_name,
                "available_models": model_names,
            }
        except Exception as e:
            return {
                "ollama": False,
                "model_loaded": False,
                "model_name": self.model_name,
                "error": str(e),
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", type=str, default=DEFAULT_QUESTION, required=False)
    parser.add_argument("--api-key", type=str, default="EMPTY", required=False)
    parser.add_argument("--model", type=str, default="text2sql", required=False)
    parser.add_argument("--host", type=str, default="127.0.0.1", required=False)
    parser.add_argument("--port", type=int, default=11434, required=False)
    args = parser.parse_args()

    client = DistilLabsLLM(
        model_name=args.model, api_key=args.api_key, host=args.host, port=args.port
    )
    print("Health:", client.check_health())
    print("Result:", client.invoke(args.question))