"use client";

import { useState, useCallback, useEffect } from "react";
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
  const [querySource, setQuerySource] = useState<"mysql" | "csv">("mysql");

  // Auto-load tables from both MySQL and CSV on mount
  useEffect(() => {
    apiClient
      .listTables()
      .then((res) => setTables(res.tables))
      .catch(() => {});
  }, []);

  // Derived counts for display
  const mysqlTables = tables.filter((t) => t.source === "mysql");
  const csvTables = tables.filter((t) => t.source === "csv");

  // --- Upload CSV ---
  const handleUpload = useCallback(async (files: File[]) => {
    setUploading(true);
    setError(null);
    try {
      await apiClient.uploadFiles(files);
      const tablesRes = await apiClient.listTables();
      setTables(tablesRes.tables);
    } catch (e: any) {
      setError(e.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  // --- Delete table (CSV only) ---
  const handleDelete = useCallback(async (name: string) => {
    setError(null);
    try {
      await apiClient.deleteTable(name);
      setTables((prev) => prev.filter((t) => t.name !== name));
    } catch (e: any) {
      setError(e.message || "Delete failed");
    }
  }, []);

  // --- Refresh MySQL schemas ---
  const handleRefresh = useCallback(async () => {
    setError(null);
    try {
      await apiClient.refreshMysqlTables();
      const tablesRes = await apiClient.listTables();
      setTables(tablesRes.tables);
    } catch (e: any) {
      setError(e.message || "Refresh failed");
    }
  }, []);

  // --- Query ---
  const handleQuery = useCallback(
    async (question: string) => {
      setQuerying(true);
      setError(null);
      setResult(null);
      try {
        const res = await apiClient.query(question, querySource);
        setResult(res);
        addToHistory({
          question,
          sql: res.sql,
          rowCount: res.row_count,
          timestamp: Date.now(),
        });
        window.dispatchEvent(new Event("text2sql:history-updated"));
      } catch (e: any) {
        setError(e.message || "Query failed");
      } finally {
        setQuerying(false);
      }
    },
    [querySource]
  );

  // --- History replay ---
  const handleHistorySelect = useCallback(
    (entry: HistoryEntry) => {
      setResult({
        sql: entry.sql,
        columns: [],
        rows: [],
        row_count: entry.rowCount,
        source: querySource,
      });
      handleQuery(entry.question);
    },
    [handleQuery, querySource]
  );

  // Check if querying is possible given current source
  const canQuery =
    querySource === "mysql"
      ? mysqlTables.length > 0
      : csvTables.length > 0;

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
                Tech Shop <span className="text-gradient">Admin</span>
              </h1>
              <p className={styles.subtitle}>
                Natural language queries on your database
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
        {/* Left panel */}
        <aside className={styles.sidebar}>
          {/* Source selector */}
          <div className={`glass-card ${styles.card}`}>
            <h2 className={styles.cardTitle}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <ellipse cx="12" cy="5" rx="9" ry="3" />
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
              </svg>
              Data Source
            </h2>
            <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
              <button
                className={`btn ${querySource === "mysql" ? "btn-primary" : "btn-ghost"} btn-sm`}
                onClick={() => setQuerySource("mysql")}
              >
                MySQL ({mysqlTables.length})
              </button>
              <button
                className={`btn ${querySource === "csv" ? "btn-primary" : "btn-ghost"} btn-sm`}
                onClick={() => setQuerySource("csv")}
              >
                CSV ({csvTables.length})
              </button>
            </div>

            {/* Refresh button for MySQL */}
            {querySource === "mysql" && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={handleRefresh}
                style={{ width: "100%", marginBottom: "12px" }}
              >
                Refresh MySQL Schema
              </button>
            )}

            {/* CSV upload (only show when CSV source is selected) */}
            {querySource === "csv" && (
              <FileUpload onUpload={handleUpload} uploading={uploading} />
            )}

            {/* Table list for active source */}
            <div className={styles.tableSection}>
              <TableList
                tables={querySource === "mysql" ? mysqlTables : csvTables}
                onDelete={handleDelete}
              />
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
              <span className="badge badge-info" style={{ marginLeft: "auto", fontSize: "0.7rem" }}>
                {querySource.toUpperCase()}
              </span>
            </h2>
            <QueryInput
              onSubmit={handleQuery}
              loading={querying}
              disabled={!canQuery}
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
                  x
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
                <div className={styles.loadingTitle}>Generating SQL...</div>
                <div className={styles.loadingText}>
                  The model is analyzing your question and {querySource === "mysql" ? "database" : "CSV"} schema
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
                {canQuery
                  ? `Type a question in natural language to query ${querySource === "mysql" ? "the Tech Shop database" : "your CSV data"}.`
                  : querySource === "mysql"
                  ? "Cannot connect to MySQL. Check if the database is running."
                  : "Upload CSV files to get started. Each file becomes a queryable table."}
              </p>
              {canQuery && (
                <div className={styles.emptySteps}>
                  <div className={styles.step}>
                    <span className={styles.stepNum}>1</span>
                    <span>Type a question (Vietnamese or English)</span>
                  </div>
                  <div className={styles.step}>
                    <span className={styles.stepNum}>2</span>
                    <span>AI generates SQL from your question</span>
                  </div>
                  <div className={styles.step}>
                    <span className={styles.stepNum}>3</span>
                    <span>See the results instantly</span>
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
