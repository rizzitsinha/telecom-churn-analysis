## Telecom Churn Analytics PoC

React + Python dashboard for analyzing telecom customer churn across 500K Indian customers.

### Architecture
- **Scripts** (run once): Generate data → Train model → Precompute dashboard JSONs
- **Backend** (FastAPI): AI-only endpoints (Gemini streaming)
- **Frontend** (React + Vite): Static JSON data + AI chat

---

## Setup & Run Order

### 1. Generate data (run once, ~2 min)
```bash
cd scripts
../venv_scripts/bin/python generate_telecom_data.py
```

### 2. Train model and generate predictions (run once, ~5 min)
```bash
../venv_scripts/bin/python churn_pipeline.py
```

### 3. Pre-compute all dashboard JSONs (run once, ~1 min)
```bash
../venv_scripts/bin/python precompute_dashboard.py
# Outputs land in frontend/public/data/
```

### 4. Start AI backend
```bash
cd ../backend
# Add your Gemini key to backend/.env
../venv_backend/bin/uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 5. Start React frontend
```bash
cd ../frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

---

### Notes
- Steps 1–3 only need to be run once. After that, only steps 4 and 5 are needed.
- The dashboard reads pre-computed JSON files as static assets. No live data pipeline.
- Only the AI chatbot and hotspot recommendations require the backend server to be running.
- Add your Gemini API key to `backend/.env` before starting the backend.
