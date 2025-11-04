# apps/backend/app.py
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import requests
from dotenv import load_dotenv

# -------------------------------------------------------------
# .env laden (apps/backend/.env)
# Erwartet:
#   BIRDEYE_API_KEY=dein_key
#   BIRDEYE_BASE=https://public-api.birdeye.so   (optional)
# -------------------------------------------------------------
load_dotenv()

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
BIRDEYE_BASE = os.getenv("BIRDEYE_BASE", "https://public-api.birdeye.so")

app = FastAPI(
    title="ProphetSolAI Backend",
    version="1.4.0",
    description="Interne API für ProphetSolAI (Demo/MVP). Enthält Test- und Fallback-Endpunkte.",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# -------------------------------------------------------------
# Models
# -------------------------------------------------------------
class AnalyzeIn(BaseModel):
    """Eingabemodell für die Demo-Analyse"""
    input: str

class TokenInfoRichIn(BaseModel):
    mint: str

# -------------------------------------------------------------
# Utils
# -------------------------------------------------------------
def _safe_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        return resp.text

def _is_valid_solana_mint(mint: str) -> bool:
    """Bevorzugt echtes Base58-Decoding, fällt sonst auf Regex zurück."""
    m = (mint or "").strip()
    if not m:
        return False
    try:
        # Versuche echtes Base58 (falls installiert: pip install base58)
        import base58  # type: ignore
        raw = base58.b58decode(m)
        return len(raw) == 32
    except Exception:
        # Fallback: Zeichenraum + sinnvolle Länge (32..44)
        import re
        if not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]+", m):
            return False
        return 32 <= len(m) <= 44

# -------------------------------------------------------------
# Endpunkte (DEINE ORIGINALEN)
# -------------------------------------------------------------
@app.get("/", summary="Root", description="Ein einfacher Ping, um zu prüfen, ob der Service läuft.")
def root():
    return {"message": "Prophecy Service läuft 🚀"}

@app.get("/health", summary="Health", description="Health-Check ohne externe Abhängigkeiten.")
def health():
    return {"ok": True}

@app.post(
    "/analyze",
    summary="Analyze",
    description="Minimaler Demo-Endpoint. Nimmt Text entgegen und gibt eine Platzhalter-‚Prophezeiung‘ zurück."
)
def analyze(payload: AnalyzeIn):
    q = (payload.input or "").strip()
    prophecy_text = f"Vorzeichen für '{q}': Frühphase. Pure Liquidität, Holder-Verteilung, DEX-Momentum prüfen."
    return JSONResponse(
        content={
            "ok": True,
            "input": q,
            "prophecy": prophecy_text,
        }
    )

@app.get(
    "/env_debug",
    summary="Env Debug",
    description="Zeigt an, ob der Birdeye-Key geladen wurde und welche BASE-URL verwendet wird."
)
def env_debug():
    key_loaded = bool(BIRDEYE_API_KEY)
    return JSONResponse(
        content={
            "env_path_exists": True,      # Hinweis: In Codespaces nicht verlässlich prüfbar → statischer Hint
            "key_loaded": key_loaded,
            "base": BIRDEYE_BASE,
        },
        status_code=200
    )

@app.get(
    "/birdeye_test",
    summary="Birdeye Test",
    description=(
        "Testet eine sehr einfache Birdeye-Anfrage (defi/tokenlist). "
        "Benötigt gültigen **BIRDEYE_API_KEY** in `apps/backend/.env`. "
        "Antwort gibt Status, Erfolg und evtl. Fehlermeldung aus."
    )
)
def birdeye_test():
    headers = {"accept": "application/json"}
    if BIRDEYE_API_KEY:
        headers["x-api-key"] = BIRDEYE_API_KEY

    try:
        url = f"{BIRDEYE_BASE}/defi/tokenlist"
        resp = requests.get(url, headers=headers, timeout=12)
        data = _safe_json(resp)
        return JSONResponse(
            content={
                "ok": True,
                "status": resp.status_code,
                "data": data if isinstance(data, dict) else {"success": False, "message": "non-JSON response"},
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"ok": False, "error": str(e)},
            status_code=500
        )

@app.get(
    "/token_info",
    summary="Kompakter Token-Überblick per Mint-Adresse",
    description=(
        "Liefert **symbol, name, price, v24hChangePercent, v24hUSD, liquidity**. "
        "Der Endpoint versucht zuerst `defi/token_overview` (planabhängig). "
        "Falls 401/403/Rate-Limit oder `success:false`, fällt er auf `defi/price` zurück.\n\n"
        "**Hinweis:** Mit Birdeye Free sind manche Felder nicht verfügbar (401/403). "
        "In dem Fall werden Felder ausgelassen und eine klare ‚reason‘ mitgegeben."
    )
)
def token_info(address: str = Query(..., description="Mint-Adresse (Solana)")):
    if not BIRDEYE_API_KEY:
        return JSONResponse(
            content={
                "ok": False,
                "error": "missing_api_key",
                "message": "BIRDEYE_API_KEY nicht gesetzt. Bitte apps/backend/.env prüfen."
            },
            status_code=400
        )

    headers = {
        "accept": "application/json",
        "x-api-key": BIRDEYE_API_KEY
    }

    def overview_req(mint: str):
        url = f"{BIRDEYE_BASE}/defi/token_overview?address={mint}"
        r = requests.get(url, headers=headers, timeout=12)
        return r

    def price_req(mint: str):
        url = f"{BIRDEYE_BASE}/defi/price?address={mint}"
        r = requests.get(url, headers=headers, timeout=12)
        return r

    # Ergebnis-Grundstruktur
    out: Dict[str, Any] = {
        "ok": True,
        "address": address,
        "source": None,
        "data": {
            "symbol": None,
            "name": None,
            "price": None,
            "v24hChangePercent": None,
            "v24hUSD": None,
            "liquidity": None,
        },
        "reasons": []
    }

    # 1) Overview versuchen
    try:
        resp = overview_req(address)
        body = _safe_json(resp)
        if resp.ok and isinstance(body, dict) and body.get("success"):
            d = body.get("data") or {}
            out["source"] = "birdeye/defi/token_overview"
            out["data"]["symbol"] = d.get("symbol")
            out["data"]["name"] = d.get("name")
            out["data"]["price"] = d.get("price") or d.get("value")
            out["data"]["v24hChangePercent"] = d.get("v24hChangePercent")
            out["data"]["v24hUSD"] = d.get("v24hUSD")
            out["data"]["liquidity"] = d.get("liquidity")
            return JSONResponse(content=out, status_code=200)
        else:
            # Keine Berechtigung oder kein Erfolg → Grund merken
            out["reasons"].append({
                "stage": "overview",
                "status": getattr(resp, "status_code", None),
                "body": body if isinstance(body, dict) else str(body),
            })
    except Exception as e:
        out["reasons"].append({"stage": "overview", "exception": str(e)})

    # 2) Fallback: Price
    try:
        resp = price_req(address)
        body = _safe_json(resp)
        if resp.ok and isinstance(body, dict) and body.get("success"):
            d = body.get("data") or {}
            out["source"] = "birdeye/defi/price"
            out["data"]["price"] = d.get("value") or d.get("price")
            return JSONResponse(content=out, status_code=200)
        else:
            out["reasons"].append({
                "stage": "price",
                "status": getattr(resp, "status_code", None),
                "body": body if isinstance(body, dict) else str(body),
            })
            # Saubere Fehlermeldung erzeugen
            msg = "Your API key is either suspended or lacks sufficient permissions to access this resource."
            if isinstance(body, dict) and body.get("message"):
                msg = body.get("message")
            return JSONResponse(
                content={
                    "ok": False,
                    "error": "birdeye_failed",
                    "overview": (out["reasons"][0] if out["reasons"] else None),
                    "price": {"success": False, "message": msg},
                },
                status_code=401 if isinstance(body, dict) and body.get("message") else 400
            )
    except Exception as e:
        out["reasons"].append({"stage": "price", "exception": str(e)})
        return JSONResponse(
            content={"ok": False, "error": "exception_price", "details": out["reasons"]},
            status_code=500
        )

# -------------------------------------------------------------
# NEU: /token_info_rich  (Free-Tier freundlich + Fallbacks)
# -------------------------------------------------------------
@app.post(
    "/token_info_rich",
    summary="Reiches Token-Profil (Free-Tier freundlich)",
    description=(
        "Gibt stets ein **stabiles JSON** zurück (crasht nicht). "
        "Strategie: Birdeye/price → Jupiter (Fallback) + Token-Meta (Solana Token List). "
        "Kennzeichnet fehlende Felder mit 'unavailable (Free-Tier)'."
    )
)
def token_info_rich(payload: TokenInfoRichIn):
    mint = (payload.mint or "").strip()
    if not _is_valid_solana_mint(mint):
        return JSONResponse(
            content={"ok": False, "data": None, "notes": ["Invalid mint: not base58/32 bytes"], "sources": []},
            status_code=400
        )

    sources, notes = [], []

    # --- 1) Birdeye price (wenn Key vorhanden) ---
    price: Optional[float] = None
    change24h: Optional[float] = None
    if BIRDEYE_API_KEY:
        try:
            url = f"{BIRDEYE_BASE}/defi/price?address={mint}"
            headers = {"accept": "application/json", "x-api-key": BIRDEYE_API_KEY}
            r = requests.get(url, headers=headers, timeout=8)
            body = _safe_json(r)
            if r.status_code in (401, 403, 429):
                sources.append({"source": "birdeye/defi/price", "status": r.status_code, "note": "rate-limit/plan"})
            elif r.ok and isinstance(body, dict) and body.get("success"):
                d = (body.get("data") or {})
                price = d.get("value") or d.get("price")
                change24h = d.get("change24h") or d.get("priceChange24h") or d.get("diff24h")
                sources.append({"source": "birdeye/defi/price", "status": r.status_code})
            else:
                sources.append({"source": "birdeye/defi/price", "status": r.status_code, "note": "no-success"})
        except Exception as e:
            sources.append({"source": "birdeye/defi/price", "error": str(e)[:160]})
    else:
        notes.append("birdeye api key missing")

    # --- 2) Jupiter Fallback (falls Preis noch None) ---
    if price is None:
        try:
            jurl = f"https://price.jup.ag/v4/price?ids={mint}"
            r = requests.get(jurl, timeout=8)
            r.raise_for_status()
            data = r.json().get("data", {})
            rec = data.get(mint)
            price = rec.get("price") if rec else None
            sources.append({"source": "jupiter/v4/price"})
        except Exception as e:
            sources.append({"source": "jupiter/v4/price", "error": str(e)[:160]})
            notes.append("price unavailable (Free-Tier / fallback failed)")

    # --- 3) Token Meta (Solana Token List) ---
    meta: Dict[str, Any] = {"symbol": None, "name": None, "decimals": None, "logo": None}
    try:
        tl_url = "https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json"
        r = requests.get(tl_url, timeout=12)
        r.raise_for_status()
        tokens = (r.json() or {}).get("tokens", [])
        t = next((t for t in tokens if t.get("address") == mint), None)
        if t:
            meta = {
                "symbol": t.get("symbol"),
                "name": t.get("name"),
                "decimals": t.get("decimals"),
                "logo": t.get("logoURI") or t.get("logoUri")
            }
        else:
            notes.append("meta unavailable (token list)")
        sources.append({"source": "solana-token-list"})
    except Exception as e:
        sources.append({"source": "solana-token-list", "error": str(e)[:160]})
        notes.append("meta fetch failed")

    # --- 4) Felder, die im Free-Tier fehlen ---
    data = {
        "mint": mint,
        "price": price,
        "change24h": change24h,
        "liquidity": "unavailable (Free-Tier)",
        "holders": "unavailable (Free-Tier)",
        "meta": meta
    }
    ok = (price is not None) or any(meta.values())
    return JSONResponse(content={"ok": ok, "data": data, "notes": notes, "sources": sources}, status_code=200)

# -------------------------------------------------------------
# Lokaler Start (nur Dev)
# -------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    # In Codespaces wird über Port-Forwarding veröffentlicht.
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
