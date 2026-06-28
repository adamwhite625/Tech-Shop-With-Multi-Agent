"use client";

import { useEffect, useState } from "react";
import { apiClient, HealthStatus } from "@/lib/api";
import styles from "./HealthBadge.module.css";

export default function HealthBadge() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [checking, setChecking] = useState(true);

  const check = async () => {
    setChecking(true);
    try {
      const h = await apiClient.health();
      setHealth(h);
    } catch {
      setHealth(null);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const isOnline = health?.ollama === true;
  const modelReady = health?.model_loaded === true;

  return (
    <div className={styles.wrapper}>
      <button className={styles.badge} onClick={check} title="Click to refresh">
        <span
          className={`${styles.dot} ${
            checking
              ? styles.dotChecking
              : isOnline && modelReady
              ? styles.dotOnline
              : isOnline
              ? styles.dotWarning
              : styles.dotOffline
          }`}
        />
        <span className={styles.label}>
          {checking
            ? "Checking…"
            : isOnline && modelReady
            ? "Model Ready"
            : isOnline
            ? "Model Not Loaded"
            : "Ollama Offline"}
        </span>
      </button>
      {health && !checking && (
        <div className={styles.tooltip}>
          <div className={styles.tooltipRow}>
            <span>Ollama</span>
            <span className={isOnline ? styles.ok : styles.fail}>
              {isOnline ? "● Connected" : "● Disconnected"}
            </span>
          </div>
          <div className={styles.tooltipRow}>
            <span>Model</span>
            <span className={modelReady ? styles.ok : styles.fail}>
              {health.model_name}
            </span>
          </div>
          <div className={styles.tooltipRow}>
            <span>Tables</span>
            <span>{health.tables_loaded}</span>
          </div>
        </div>
      )}
    </div>
  );
}
