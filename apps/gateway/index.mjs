import express from "express";
import cors from "cors";
import fetch from "node-fetch";

const app = express();
app.use(express.json());
app.use(cors()); // erlaubt Aufrufe vom Frontend

// === Env Variablen ===
const PORT = process.env.PORT || process.env.GATEWAY_PORT || 8082;
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

// === Healthcheck ===
app.get("/health", (_req, res) => res.json({ ok: true }));

// === Root-Route ===
app.get("/", (_req, res) => {
  res.json({
    ok: true,
    service: "ProphetSolAI Gateway läuft ✅",
    backend: BACKEND_URL,
  });
});

// === Analyse-Endpoint ===
app.post("/analyze", async (req, res) => {
  try {
    const r = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(req.body),
    });
    const data = await r.json();
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: "gateway_failed", detail: String(e) });
  }
});

// === Alte Test-Route (/prophecy) ===
app.get("/prophecy", async (_req, res) => {
  try {
    const r = await fetch(`${BACKEND_URL}/`);
    const data = await r.json();
    res.json({ ok: true, backend: data });
  } catch (e) {
    res.status(502).json({ ok: false, error: String(e) });
  }
});

// === Server starten ===
app.listen(PORT, "0.0.0.0", () => {
  console.log(`Gateway läuft auf Port ${PORT} -> ${BACKEND_URL}`);
});