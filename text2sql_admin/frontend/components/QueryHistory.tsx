"use client";

import { useState, useEffect } from "react";
import styles from "./QueryHistory.module.css";

export interface HistoryEntry {
  id: string;
  question: string;
  sql: string;
  rowCount: number;
  timestamp: number;
}

interface Props {
  onSelect: (entry: HistoryEntry) => void;
}

const STORAGE_KEY = "text2sql_history";

export function addToHistory(entry: Omit<HistoryEntry, "id">) {
  const existing = getHistory();
  const newEntry: HistoryEntry = {
    ...entry,
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
  };
  const updated = [newEntry, ...existing].slice(0, 50); // keep last 50
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }
}

export function getHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function clearHistory() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(STORAGE_KEY);
  }
}

export default function QueryHistory({ onSelect }: Props) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // Reload history on each render and listen for storage events
  useEffect(() => {
    setHistory(getHistory());

    const handleStorage = () => setHistory(getHistory());
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  // Expose a refresh function via custom event
  useEffect(() => {
    const refresh = () => setHistory(getHistory());
    window.addEventListener("text2sql:history-updated", refresh);
    return () => window.removeEventListener("text2sql:history-updated", refresh);
  }, []);

  const handleClear = () => {
    clearHistory();
    setHistory([]);
  };

  const formatTime = (ts: number) => {
    const d = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return d.toLocaleDateString();
  };

  return (
    <div className={styles.wrapper}>
      <button
        className={styles.toggle}
        onClick={() => setIsOpen(!isOpen)}
        title="Query History"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <span>History</span>
        {history.length > 0 && (
          <span className={styles.badge}>{history.length}</span>
        )}
        <svg
          className={`${styles.chevron} ${isOpen ? styles.chevronOpen : ""}`}
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div className={styles.panel}>
          {history.length === 0 ? (
            <div className={styles.empty}>No queries yet</div>
          ) : (
            <>
              <div className={styles.panelHeader}>
                <span className={styles.panelTitle}>Recent Queries</span>
                <button className={`btn btn-ghost btn-sm`} onClick={handleClear}>
                  Clear All
                </button>
              </div>
              <div className={styles.list}>
                {history.map((entry) => (
                  <button
                    key={entry.id}
                    className={styles.item}
                    onClick={() => onSelect(entry)}
                  >
                    <span className={styles.question}>{entry.question}</span>
                    <span className={styles.meta}>
                      {entry.rowCount} rows &middot; {formatTime(entry.timestamp)}
                    </span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
