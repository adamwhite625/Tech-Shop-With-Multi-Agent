"use client";

import styles from "./SqlPreview.module.css";

interface Props {
  sql: string;
}

/** Simple SQL keyword highlighter (no external deps). */
function highlightSQL(sql: string): string {
  const keywords = [
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "FULL", "CROSS", "ON", "AND", "OR", "NOT", "IN", "IS", "NULL", "AS",
    "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET", "DISTINCT",
    "UNION", "ALL", "INSERT", "UPDATE", "DELETE", "CREATE", "TABLE",
    "DROP", "ALTER", "INDEX", "INTO", "VALUES", "SET", "BETWEEN", "LIKE",
    "EXISTS", "CASE", "WHEN", "THEN", "ELSE", "END", "ASC", "DESC",
    "COUNT", "SUM", "AVG", "MIN", "MAX", "CAST", "COALESCE",
    "WITH", "RECURSIVE", "OVER", "PARTITION", "ROW_NUMBER", "RANK",
  ];

  const functions = [
    "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "CAST",
    "LOWER", "UPPER", "TRIM", "LENGTH", "SUBSTR", "REPLACE",
    "ROUND", "ABS", "IFNULL", "NULLIF", "TYPEOF", "DATE",
    "STRFTIME", "JULIANDAY", "ROW_NUMBER", "RANK", "DENSE_RANK",
  ];

  let result = sql;

  // Escape HTML
  result = result.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // Highlight strings
  result = result.replace(/'([^']*)'/g, `<span class="sql-string">'$1'</span>`);

  // Highlight numbers (standalone)
  result = result.replace(/\b(\d+\.?\d*)\b/g, `<span class="sql-number">$1</span>`);

  // Highlight functions (word followed by open paren)
  const fnPattern = new RegExp(`\\b(${functions.join("|")})\\s*\\(`, "gi");
  result = result.replace(fnPattern, (match, fn) => {
    return `<span class="sql-function">${fn}</span>(`;
  });

  // Highlight keywords
  const kwPattern = new RegExp(`\\b(${keywords.join("|")})\\b`, "gi");
  result = result.replace(kwPattern, (match) => {
    // Don't re-highlight if already inside a span
    return `<span class="sql-keyword">${match.toUpperCase()}</span>`;
  });

  return result;
}

export default function SqlPreview({ sql }: Props) {
  if (!sql) return null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
        <span>Generated SQL</span>
        <button
          className={`btn btn-ghost btn-sm ${styles.copyBtn}`}
          onClick={() => navigator.clipboard.writeText(sql)}
          title="Copy SQL"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          Copy
        </button>
      </div>
      <pre
        className={`code-block ${styles.code}`}
        dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }}
      />
    </div>
  );
}
