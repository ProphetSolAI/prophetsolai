// apps/frontend/src/app/page.tsx
'use client';

import { useState } from 'react';
import styles from './page.module.css';

// Basis-URL aus .env holen und trailing Slashes entfernen
const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE ??
  (typeof window !== 'undefined' ? window.location.origin : '')
).replace(/\/+$/, '');

type GatewayResponse = {
  ok: boolean;
  gateway?: 'ok';
  backend?: unknown;
  error?: string;
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GatewayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/prophecy`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data: GatewayResponse = await res.json();
      setResult(data);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24, maxWidth: 800, margin: '0 auto', fontFamily: 'system-ui' }}>
      <h1 style={{ marginBottom: 8 }}>ProphetSolAI — Verbindungstest</h1>
      <p style={{ marginBottom: 16 }}>
        API_BASE: <code>{API_BASE}</code>
      </p>

      <button
  onClick={handleCheck}
  disabled={loading}
  className={styles.btn}

>
  {loading ? 'Prüfe…' : 'Backend testen (/prophecy)'}
</button>


    {error && (
  <pre className={styles.errorPanel}>
    {error}
  </pre>
)}

     {result && (
  <pre className={styles.panel}>
    {JSON.stringify(result, null, 2)}
  </pre>
)}
    </main>
  );
}
