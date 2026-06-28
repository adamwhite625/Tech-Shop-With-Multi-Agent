"use client";

import { useCallback, useState, useRef } from "react";
import styles from "./FileUpload.module.css";

interface Props {
  onUpload: (files: File[]) => Promise<void>;
  uploading: boolean;
}

export default function FileUpload({ onUpload, uploading }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList || uploading) return;
      const csvFiles = Array.from(fileList).filter((f) =>
        f.name.toLowerCase().endsWith(".csv")
      );
      if (csvFiles.length === 0) return;
      onUpload(csvFiles);
    },
    [onUpload, uploading]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  return (
    <div
      className={`${styles.dropzone} ${dragActive ? styles.active : ""} ${
        uploading ? styles.uploading : ""
      }`}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        multiple
        className={styles.input}
        onChange={(e) => handleFiles(e.target.files)}
        disabled={uploading}
      />

      <div className={styles.icon}>
        {uploading ? (
          <div className="spinner spinner-lg" />
        ) : (
          <svg
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        )}
      </div>

      <div className={styles.text}>
        {uploading ? (
          <span>Uploading files…</span>
        ) : (
          <>
            <span className={styles.primary}>
              Drop CSV files here or <span className={styles.link}>browse</span>
            </span>
            <span className={styles.secondary}>
              Supports multiple files. Each file becomes a table.
            </span>
          </>
        )}
      </div>
    </div>
  );
}
