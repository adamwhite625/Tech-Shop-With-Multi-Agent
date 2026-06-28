"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./QueryInput.module.css";

interface Props {
  onSubmit: (question: string) => void;
  loading: boolean;
  disabled: boolean;
}

export default function QueryInput({ onSubmit, loading, disabled }: Props) {
  const [question, setQuestion] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [question]);

  const handleSubmit = () => {
    const trimmed = question.trim();
    if (!trimmed || loading || disabled) return;
    onSubmit(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.inputRow}>
        <textarea
          ref={textareaRef}
          className={`textarea ${styles.textarea}`}
          placeholder={
            disabled
              ? "Upload CSV files first to start querying…"
              : "Ask a question about your data… (e.g., What is the average salary by department?)"
          }
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || disabled}
          rows={1}
        />
        <button
          className={`btn btn-primary ${styles.submitBtn}`}
          onClick={handleSubmit}
          disabled={!question.trim() || loading || disabled}
          title="Send query (Enter)"
        >
          {loading ? (
            <div className="spinner" />
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>
      <div className={styles.hint}>
        Press <kbd className={styles.kbd}>Enter</kbd> to send &middot;{" "}
        <kbd className={styles.kbd}>Shift+Enter</kbd> for new line
      </div>
    </div>
  );
}
