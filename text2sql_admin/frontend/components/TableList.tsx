"use client";

import { useState } from "react";
import { TableInfo } from "@/lib/api";
import styles from "./TableList.module.css";

interface Props {
  tables: TableInfo[];
  onDelete: (name: string) => void;
}

export default function TableList({ tables, onDelete }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (tables.length === 0) {
    return (
      <div className={styles.empty}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
        </svg>
        <span>No tables loaded yet</span>
      </div>
    );
  }

  return (
    <div className={styles.list}>
      {tables.map((t) => (
        <div
          key={t.name}
          className={`${styles.item} ${expanded === t.name ? styles.itemExpanded : ""}`}
        >
          <div
            className={styles.header}
            onClick={() => setExpanded(expanded === t.name ? null : t.name)}
          >
            <div className={styles.info}>
              <svg
                className={`${styles.chevron} ${expanded === t.name ? styles.chevronOpen : ""}`}
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
              <span className={styles.tableName}>{t.name}</span>
              <span className={styles.rowCount}>{t.row_count} rows</span>
            </div>
            <button
              className={`btn btn-danger btn-sm ${styles.deleteBtn}`}
              onClick={(e) => {
                e.stopPropagation();
                onDelete(t.name);
              }}
              title="Remove table"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6" />
                <path d="M10 11v6" />
                <path d="M14 11v6" />
              </svg>
            </button>
          </div>
          {expanded === t.name && (
            <div className={styles.schema}>
              <pre className="code-block">{t.schema}</pre>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
