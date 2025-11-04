# 🧠 ProphetSolAI 🔮  
**Solana × AI Analysis Project**

ProphetSolAI fuses meme culture with real AI utility.  
It delivers AI-powered insights and “prophecies” for Solana tokens and smart contracts —  
bridging humor, data, and technology into one intelligent ecosystem.

---

### 🚀 Current Progress (as of Nov 4, 2025)
✅ **API Gateway** connected and stable  
✅ **Backend** live with `/token_info_rich` (Free-Tier friendly)  
✅ **Prophecy Service** running successfully  
⚙️ **Next step:** connect frontend input field → real-time token analysis & prophecy display  
🧱 **Infrastructure:** Docker + Codespaces + .env fully configured

---

### ⚡ Tech Stack
- **Backend:** FastAPI (Python)  
- **Frontend:** Next.js (TypeScript, Tailwind)  
- **Blockchain:** Solana (Helius, Birdeye, Jupiter integrations)  
- **Hosting:** GitHub Codespaces / Docker (Dev & Prod)

---

### 🧩 Key API Endpoints
| Method | Route | Description |
|--------|--------|-------------|
| `GET` | `/` | Root check — “Prophecy Service running 🚀” |
| `GET` | `/health` | Simple health check |
| `POST` | `/analyze` | Basic text-to-prophecy endpoint |
| `GET` | `/env_debug` | Check .env configuration and API key |
| `GET` | `/birdeye_test` | Test Birdeye API connectivity |
| `GET` | `/token_info` | Token info (limited on Free Tier) |
| `POST` | `/token_info_rich` | Rich token profile (Jupiter + Token List fallback) ✅ |

---

Made with ⚡ by **ProphetSolAI**
