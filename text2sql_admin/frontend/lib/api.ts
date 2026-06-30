const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010";

export interface TableInfo {
  name: string;
  schema: string;
  row_count: number;
  source: "mysql" | "csv";
  columns?: { name: string; type: string }[];
  filename?: string;
}

export interface QueryResult {
  sql: string;
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
  source: string;
}

export interface HealthStatus {
  status: string;
  ollama: boolean;
  model_loaded: boolean;
  model_name: string;
  mysql_connected: boolean;
  mysql_tables: number;
  csv_tables: number;
}

export interface UploadResponse {
  uploaded: number;
  tables: {
    filename: string;
    table_name: string;
    schema: string;
    columns: { name: string; type: string }[];
    row_count: number;
    source: string;
  }[];
}

class ApiClient {
  private base: string;

  constructor() {
    this.base = API_BASE;
  }

  /* Check backend and LLM health status */
  async health(): Promise<HealthStatus> {
    const res = await fetch(`${this.base}/api/health`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
    return res.json();
  }

  /* Upload CSV files for ad-hoc analysis */
  async uploadFiles(files: File[]): Promise<UploadResponse> {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    const res = await fetch(`${this.base}/api/upload`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Upload failed: ${res.status}`);
    }
    return res.json();
  }

  /* List all tables from MySQL and CSV sources */
  async listTables(): Promise<{ tables: TableInfo[] }> {
    const res = await fetch(`${this.base}/api/tables`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to list tables: ${res.status}`);
    return res.json();
  }

  /* Reload MySQL schemas after database changes */
  async refreshMysqlTables(): Promise<{ refreshed: number; tables: string[] }> {
    const res = await fetch(`${this.base}/api/tables/refresh`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`Failed to refresh tables: ${res.status}`);
    return res.json();
  }

  /* Delete a CSV-uploaded table */
  async deleteTable(name: string): Promise<void> {
    const res = await fetch(`${this.base}/api/tables/${name}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Failed to delete table: ${res.status}`);
    }
  }

  /* Send a natural language question and get SQL + results */
  async query(question: string, source: "mysql" | "csv" = "mysql"): Promise<QueryResult> {
    const res = await fetch(`${this.base}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, source }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Query failed: ${res.status}`);
    }
    return res.json();
  }
}

export const apiClient = new ApiClient();
