# Intelli-Credit — AI Credit Decisioning Platform

> Automates corporate loan appraisal from 2-3 weeks to under 5 minutes

## Tech Stack
Python · FastAPI · React.js · XGBoost · OpenAI GPT · FAISS · JWT

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Demo
- URL: http://localhost:3000
- Click **Try Demo Account** to login instantly

## Environment Variables
Copy `backend/.env.example` to `backend/.env` and fill in your API keys