"use client";

import { useState, useCallback } from "react";
import { apiClient, TableInfo, QueryResult } from "@/lib/api";
import { addToHistory, HistoryEntry } from "@/components/QueryHistory";
import HealthBadge from "@/components/HealthBadge";
import FileUpload from "@/components/FileUpload";
import TableList from "@/components/TableList";
import QueryInput from "@/components/QueryInput";
import SqlPreview from "@/components/SqlPreview";
import ResultsTable from "@/components/ResultsTable";
import QueryHistory from "@/components/QueryHistory";
import styles from "./page.module.css";

export default function Home() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [querying, setQuerying] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // --- Upload ---
  const handleUpload = useCallback(async (files: File[]) => {
    setUploading(true);
    setError(null);
    try {
      const res = await apiClient.uploadFiles(files);
      // Refresh table list
      const tablesRes = await apiClient.listTables();
      setTables(tablesRes.tables);
    } catch (e: any) {
      setError(e.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  // --- Delete table ---
  const handleDelete = useCallback(async (name: string) => {
    setError(null);
    try {
      await apiClient.deleteTable(name);
      setTables((prev) => prev.filter((t) => t.name !== name));
    } catch (e: any) {
      setError(e.message || "Delete failed");
    }
  }, []);

  // --- Query ---
  const handleQuery = useCallback(async (question: string) => {
    setQuerying(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiClient.query(question);
      setResult(res);
      // Save to history
      addToHistory({
        question,
        sql: res.sql,
        rowCount: res.row_count,
        timestamp: Date.now(),
      });
      // Notify history component
      window.dispatchEvent(new Event("text2sql:history-updated"));
    } catch (e: any) {
      setError(e.message || "Query failed");
    } finally {
      setQuerying(false);
    }
  }, []);

  // --- History replay ---
  const handleHistorySelect = useCallback((entry: HistoryEntry) => {
    setResult({
      sql: entry.sql,
      columns: [],
      rows: [],
      row_count: entry.rowCount,
    });
    // Re-run the query to get fresh results
    handleQuery(entry.question);
  }, [handleQuery]);

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logo}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#06b6d4" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
              <ellipse cx="12" cy="5" rx="9" ry="3" />
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
            </svg>
            <div>
              <h1 className={styles.title}>
                Text<span className="text-gradient">2</span>SQL
              </h1>
              <p className={styles.subtitle}>
                Natural language queries on your data
              </p>
            </div>
          </div>
        </div>
        <div className={styles.headerRight}>
          <HealthBadge />
        </div>
      </header>

      {/* Main content */}
      <main className={styles.main}>
        {/* Left panel — Data */}
        <aside className={styles.sidebar}>
          <div className={`glass-card ${styles.card}`}>
            <h2 className={styles.cardTitle}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
              Data Sources
            </h2>
            <FileUpload onUpload={handleUpload} uploading={uploading} />
            <div className={styles.tableSection}>
              <TableList tables={tables} onDelete={handleDelete} />
            </div>
          </div>

          <div className={`glass-card ${styles.card}`}>
            <QueryHistory onSelect={handleHistorySelect} />
          </div>
        </aside>

        {/* Right panel — Query & Results */}
        <section className={styles.content}>
          <div className={`glass-card ${styles.card}`}>
            <h2 className={styles.cardTitle}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              Ask a Question
            </h2>
            <QueryInput
              onSubmit={handleQuery}
              loading={querying}
              disabled={tables.length === 0}
            />
          </div>

          {/* Error */}
          {error && (
            <div className={`glass-card ${styles.card} ${styles.errorCard}`}>
              <div className={styles.errorContent}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="15" y1="9" x2="9" y2="15" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                </svg>
                <div>
                  <div className={styles.errorTitle}>Error</div>
                  <div className={styles.errorMessage}>{error}</div>
                </div>
                <button
                  className={`btn btn-ghost btn-sm ${styles.errorDismiss}`}
                  onClick={() => setError(null)}
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* SQL Preview */}
          {result?.sql && (
            <div className={`glass-card ${styles.card}`}>
              <SqlPreview sql={result.sql} />
            </div>
          )}

          {/* Results Table */}
          {result && result.columns.length > 0 && (
            <div className={`glass-card ${styles.card}`}>
              <ResultsTable
                columns={result.columns}
                rows={result.rows}
                rowCount={result.row_count}
              />
            </div>
          )}

          {/* Loading state */}
          {querying && (
            <div className={`glass-card ${styles.card} ${styles.loadingCard}`}>
              <div className="spinner spinner-lg" />
              <div>
                <div className={styles.loadingTitle}>Generating SQL…</div>
                <div className={styles.loadingText}>
                  The model is analyzing your question and schema
                </div>
              </div>
            </div>
          )}

          {/* Empty state */}
          {!result && !querying && !error && (
            <div className={`glass-card ${styles.card} ${styles.emptyState}`}>
              <div className={styles.emptyIcon}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="16 18 22 12 16 6" />
                  <polyline points="8 6 2 12 8 18" />
                </svg>
              </div>
              <h3 className={styles.emptyTitle}>Ready to Query</h3>
              <p className={styles.emptyText}>
                {tables.length === 0
                  ? "Upload CSV files to get started. Each file becomes a queryable table."
                  : "Type a natural language question about your data and press Enter."}
              </p>
              {tables.length === 0 && (
                <div className={styles.emptySteps}>
                  <div className={styles.step}>
                    <span className={styles.stepNum}>1</span>
                    <span>Upload CSV files</span>
                  </div>
                  <div className={styles.step}>
                    <span className={styles.stepNum}>2</span>
                    <span>Ask a question in natural language</span>
                  </div>
                  <div className={styles.step}>
                    <span className={styles.stepNum}>3</span>
                    <span>Get SQL + results instantly</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
