import express from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import axios from "axios";

const app = express();
app.use(cors());
app.use(helmet());
app.use(morgan("dev"));
app.use(express.json());

const PORT = process.env.PORT || 8082;
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

app.get("/", (_req, res) => {
  res.json({ message: "API Gateway läuft 🚀" });
});

// Healthcheck
app.get("/healthz", (_req, res) => res.json({ ok: true }));

// Neuer Endpoint: Proxy zum FastAPI-Backend
app.get("/prophecy", async (_req, res) => {
  try {
    const r = await axios.get(`${BACKEND_URL}/`);
    return res.json({
      ok: true,
      gateway: "ok",
      backend: r.data,
    });
  } catch (err) {
    return res.status(502).json({
      ok: false,
      error: String(err),
    });
  }
});

app.listen(PORT, () => {
  console.log(`API Gateway läuft auf Port ${PORT}`);
});