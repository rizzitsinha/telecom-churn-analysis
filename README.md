## Telecom Churn Analytics PoC

A consulting-grade, full-stack churn analytics platform built for a simulated Indian telecom market (Jio/Airtel/Vi product structures). Trained a multiclass XGBoost/Random Forest classifier on a synthesized 500K-row dataset with 45 features, then surfaced insights through a 7-page React dashboard with AI-powered strategic recommendations.

Built as part of an AI/ML internship at Virtusa.

### What it does
- **Churn prediction** — Multiclass classifier optimized for macro F1, trained on realistic Indian telecom data with features like plan type, ARPU, data usage, and regional market share
- **Consulting dashboard** — 7-page React interface covering customer segmentation, retention ROI planning, bundle upsell analysis, and seasonal churn risk modeling
- **AI chatbot** — Context-aware Gemini chatbot that streams real-time strategic retention advice per segment
- **Hotspot recommendations** — Clickable regional hotspot system highlighting high-churn segments with actionable recommendations
- **Decoupled architecture** — Full data pipeline precomputed into static JSONs; backend only handles AI endpoints, keeping the dashboard fast and backend-free for most interactions


![Overview Dashboard Screenshot](/readme_images/overview.png)
*Overview Dashboard*

![Retention Planner Screenshot](/readme_images/retention_planner_ss.png)
*Retention Planner*

![AI Hotspot Recommendation Screenshot](/readme_images/ai_hotspot_rec_segmentbleeding.png)
*AI Hotspot Recommendation*


### Tech Stack
`XGBoost` `scikit-learn` `SHAP` `pandas` `FastAPI` `Google Gemini API` `React` `Vite` `Python`
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
