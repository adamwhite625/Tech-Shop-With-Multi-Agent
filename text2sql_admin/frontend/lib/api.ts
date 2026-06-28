const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TableInfo {
  name: string;
  schema: string;
  row_count: number;
  columns?: { name: string; type: string }[];
  filename?: string;
}

export interface QueryResult {
  sql: string;
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
}

export interface HealthStatus {
  status: string;
  ollama: boolean;
  model_loaded: boolean;
  model_name: string;
  tables_loaded: number;
}

export interface UploadResponse {
  uploaded: number;
  tables: {
    filename: string;
    table_name: string;
    schema: string;
    columns: { name: string; type: string }[];
    row_count: number;
  }[];
}

class ApiClient {
  private base: string;

  constructor() {
    this.base = API_BASE;
  }

  async health(): Promise<HealthStatus> {
    const res = await fetch(`${this.base}/api/health`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
    return res.json();
  }

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

  async listTables(): Promise<{ tables: TableInfo[] }> {
    const res = await fetch(`${this.base}/api/tables`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to list tables: ${res.status}`);
    return res.json();
  }

  async deleteTable(name: string): Promise<void> {
    const res = await fetch(`${this.base}/api/tables/${name}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Failed to delete table: ${res.status}`);
    }
  }

  async query(question: string): Promise<QueryResult> {
    const res = await fetch(`${this.base}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Query failed: ${res.status}`);
    }
    return res.json();
  }
}

export const apiClient = new ApiClient();
