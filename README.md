# ⚖ LexAI — Multimodal Courtroom Intelligence Platform

> *"The most innovative LegalTech AI project ever built"*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-yellow.svg)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What Problem Does This Solve?

Indian courts handle **over 50 million pending cases**. Legal teams waste thousands of hours on:
- Manual document review and entity extraction
- Searching through case law for relevant precedents
- Drafting repetitive arguments and filings
- Assessing case strength and predicting outcomes

**LexAI eliminates all of this** — replacing days of legal research with seconds of AI-powered analysis.

---

## 🌟 Why This Is Unique (Never Built Before)

| Feature | LexAI | Other Tools |
|---------|-------|-------------|
| Multimodal Evidence Analysis | ✅ PDF + Image + Audio | ❌ Text only |
| GPT-4V Forensic Evidence Analysis | ✅ | ❌ |
| Whisper Testimony Transcription | ✅ | ❌ |
| AI Prosecution + Defense Arguments | ✅ Both sides | ❌ |
| Cross-Examination Generator | ✅ 15+ questions | ❌ |
| ML Verdict Prediction + SHAP | ✅ | ❌ |
| Indian Legal Database (RAG) | ✅ IPC + CrPC + Precedents | ❌ |
| Scenario Simulator (What-If) | ✅ | ❌ |
| Complete FastAPI + Streamlit | ✅ | ❌ |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LexAI Platform                          │
├─────────────────┬───────────────────┬───────────────────────┤
│  STREAMLIT UI   │    FASTAPI BACKEND │    DATA LAYER         │
│                 │                   │                       │
│ Case Dashboard  │ /api/v1/cases     │ SQLite/PostgreSQL      │
│ Evidence Room   │ /api/v1/evidence  │ FAISS Vector Index    │
│ Argument Studio │ /api/v1/arguments │ Legal JSON Database   │
│ Verdict Pred.   │ /api/v1/verdict   │ Case Files            │
│ Legal Research  │ /api/v1/research  │ ML Models (.pkl)      │
│ Case Timeline   │ /api/v1/health    │                       │
├─────────────────┴───────────────────┴───────────────────────┤
│                    AI ENGINE                                │
│                                                             │
│  Groq Llama3-70B    GPT-4V Vision    Whisper ASR           │
│  (Arguments/RAG)    (Evidence)       (Testimony)           │
│                                                             │
│  sentence-transformers    FAISS    RandomForest+XGBoost    │
│  (Embeddings)             (Search) (Verdict Prediction)    │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 📄 Document Intelligence
- PDF, DOCX, TXT extraction with PyMuPDF
- Named Entity Recognition (spaCy): persons, dates, amounts, IPC sections
- Auto-identification of applicable legal charges
- LLM-powered document summaries

### 🖼 Vision Evidence Analysis (GPT-4V)
- Forensic analysis of evidence photographs
- EXIF metadata extraction and tampering detection
- Evidence strength scoring (1-10)
- Chain of custody assessment

### 🎵 Audio Testimony (Whisper)
- Transcription with word-level timestamps
- Cross-witness inconsistency detection
- Key statement extraction
- Credibility scoring

### ⚔ AI Argument Generation
- Full prosecution case structure (opening → closing)
- Full defense strategy (counter-arguments, acquittal grounds)
- 15+ cross-examination questions per witness
- Argument strength radar chart comparison
- 3 styles: Aggressive / Conservative / Balanced

### 🎯 Verdict Prediction (ML Ensemble)
- Random Forest + Logistic Regression + XGBoost
- SHAP explainability for each feature
- Scenario simulator ("What if forensic evidence is added?")
- Sentence estimation and appeal ground suggestions

### 📚 Legal RAG (Indian Law)
- 50+ IPC sections indexed in FAISS
- 30+ Supreme Court precedents
- 20+ recent SC judgments
- Semantic search with relevance scoring

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM (Primary) | Groq Llama3-70B (FREE) |
| Vision | GPT-4o / GPT-4V |
| Audio | OpenAI Whisper (local) |
| Embeddings | sentence-transformers MiniLM-L6 |
| Vector DB | FAISS |
| ML Models | scikit-learn + XGBoost + SHAP |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit + Plotly |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Document Processing | PyMuPDF + Tesseract OCR |
| Reports | ReportLab + Jinja2 |

---

## 📁 Project Structure

```
lexai-courtroom/
├── config/          # YAML configuration
├── data/
│   ├── cases/       # Case files (PDFs, images, audio)
│   ├── legal_database/ # IPC, CrPC, precedents JSON
│   └── processed/   # Embeddings, models, transcripts
├── src/             # Core processing modules
├── llm/             # LLM clients (Groq, OpenAI, Vision)
├── rag/             # RAG pipeline (embedder, FAISS, retriever)
├── database/        # SQLAlchemy models and CRUD
├── api/             # FastAPI backend
├── dashboard/       # Streamlit frontend
├── notebooks/       # Jupyter demos
├── scripts/         # Setup and data generation
└── tests/           # pytest test suite
```

---

## ⚡ Quick Start

### 1. Clone and setup
```bash
git clone <your-repo>
cd lexai-courtroom
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)
# Optionally add OPENAI_API_KEY for GPT-4V image analysis
```

### 3. Build legal database
```bash
python scripts/build_legal_database.py
```

### 4. Generate sample cases
```bash
python scripts/generate_sample_cases.py
```

### 5. Train ML models and launch
```bash
python src/verdict_predictor.py  # Train models
streamlit run dashboard/app.py   # Launch dashboard
```

### 6. (Optional) Launch API
```bash
uvicorn api.main:app --reload
# Visit: http://localhost:8080/docs
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/cases/create` | Create new case |
| POST | `/api/v1/cases/{id}/upload` | Upload case files |
| GET | `/api/v1/cases/{id}` | Get case details |
| POST | `/api/v1/arguments/generate` | Generate arguments |
| POST | `/api/v1/arguments/cross-examine` | Cross-exam questions |
| POST | `/api/v1/verdict/predict` | Predict verdict |
| POST | `/api/v1/verdict/simulate` | What-if scenarios |
| GET | `/api/v1/verdict/explain/{id}` | SHAP explanation |
| POST | `/api/v1/research/precedents` | Search precedents |
| POST | `/api/v1/research/sections` | Search IPC sections |
| POST | `/api/v1/research/ask` | Ask legal AI |

---

## 🧪 Sample Case Demo

1. Launch dashboard: `streamlit run dashboard/app.py`
2. Select **CASE-2024-CRM-002** (IPC 420 Fraud case) from sidebar
3. Go to **Case Dashboard** → Upload `data/cases/sample_cases/case_002/fir_report.pdf`
4. Watch entity extraction and legal charge identification
5. Go to **Argument Studio** → Click "Generate Prosecution" and "Generate Defense"
6. Go to **Verdict Predictor** → Click "Predict Verdict" and explore scenarios
7. Go to **Legal Research** → Search "cheating and fraud Section 420"
8. Download complete HTML case report

---

## 🐳 Docker Deployment

```bash
cd docker
cp ../.env.example ../.env  # Add your API keys
docker-compose up --build
# Dashboard: http://localhost:8501
# API: http://localhost:8080
```

---

## 🚀 Future Roadmap

- [ ] Real-time court hearing transcription
- [ ] Hindi/regional language support
- [ ] Integration with eCourts API
- [ ] Case outcome database (actual verdicts)
- [ ] Lawyer matching algorithm
- [ ] Mobile app (React Native)
- [ ] Integration with Bar Council databases

---

## 👤 Author

**Built for AI Engineer Portfolio** | LexAI v1.0.0

*Powered by: Groq Llama3-70B + GPT-4V + Whisper + LangChain + FAISS + RAG*

---

## 📄 License

MIT License — Free to use for educational and portfolio purposes.

---

> ⚠️ **Disclaimer:** LexAI is an AI research tool for legal research purposes only.
> It does not constitute legal advice. Always consult a qualified advocate for legal matters.
