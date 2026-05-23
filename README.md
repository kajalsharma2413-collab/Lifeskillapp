# Life Skills World 🌟

An AI-powered life skills learning platform for children aged 8–14. Parents register their children, track progress, and receive insights while kids learn through interactive quizzes, comics, diary entries, games, and AI mentoring.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [User Roles](#user-roles)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Clone the Repository](#clone-the-repository)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [AI Features](#ai-features)
- [Deployment](#deployment)
  - [Backend — Render](#backend--render)
  - [Frontend — Vercel](#frontend--vercel)
- [Scripts](#scripts)

---

## Overview

Life Skills World teaches children essential life skills — financial literacy, personal safety, problem solving, emotional intelligence, and more — through an engaging, child-friendly interface backed by AI. A parent dashboard provides oversight, while an admin panel manages content and monitors platform health.

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.13) |
| Database | Cloud Firestore (Firebase) |
| Authentication | Firebase Auth + JWT |
| AI / LLM | Ollama (`gemma4:31b-cloud`) |
| Embeddings | Ollama (`nomic-embed-text`) |
| Vector Store | Pinecone |
| RAG Orchestration | LangChain + LangGraph |
| Web Search | Tavily |
| Voice | VAPI |
| Package Manager | uv |

### Frontend
| Layer | Technology |
|---|---|
| Framework | Vue 3 |
| Build Tool | Vite |
| Styling | Tailwind CSS (Dracula theme) |
| Auth | Firebase JS SDK |
| Fonts | Fredoka, Comic Neue |

---

## Project Structure

```
Lifeskillapp/
├── backend/                          # FastAPI backend (deploy to Render)
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies/
│   │   │   │   ├── ai/
│   │   │   │   │   ├── mentor_chatbot/     # AI mentor (Ollama + LangGraph)
│   │   │   │   │   ├── problem_solving/    # Smart question generator
│   │   │   │   │   ├── rag_chatbot/        # RAG agent (Pinecone + Tavily)
│   │   │   │   │   └── diary_summarizer.py # Diary mood analysis
│   │   │   │   └── auth.py                 # JWT + Firebase token verification
│   │   │   └── v1/                         # All REST endpoints
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── admin.py
│   │   │       ├── admin_dashboard.py
│   │   │       ├── quiz.py
│   │   │       ├── diary.py
│   │   │       ├── finance.py
│   │   │       ├── safety.py
│   │   │       ├── skills.py
│   │   │       ├── mentor_chatbot.py
│   │   │       ├── rag_chat.py
│   │   │       ├── problem_solving.py
│   │   │       ├── parent.py
│   │   │       ├── vapi.py
│   │   │       └── router.py
│   │   ├── config/
│   │   │   ├── firebase.py             # Firebase Admin SDK init
│   │   │   ├── settings.py             # Pydantic settings (reads .env)
│   │   │   └── logging.py              # Loguru logger
│   │   ├── models/                     # Pydantic data models
│   │   ├── schemas/                    # Request/response schemas
│   │   ├── services/                   # Business logic layer
│   │   └── utils/                      # Security, pagination, quiz utils
│   ├── scripts/
│   │   └── create_admin.py             # Create first admin user
│   ├── assets/
│   │   └── Life Skills App API.postman_collection.json
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env                            # (not committed)
│
└── frontend/                           # Vue 3 frontend (deploy to Vercel)
    ├── src/
    │   ├── components/                 # All Vue components
    │   │   ├── HomeView.vue
    │   │   ├── StudentDashboard.vue
    │   │   ├── ParentDashboard.vue
    │   │   ├── AdminDashboard.vue
    │   │   ├── MentorChatbot.vue
    │   │   ├── ChatBot.vue             # RAG chatbot
    │   │   ├── DiaryEntry.vue
    │   │   ├── FinancialLiteracy.vue
    │   │   ├── SafetySkills.vue
    │   │   ├── ProblemSolving.vue
    │   │   └── ...
    │   ├── router/index.js
    │   ├── stores/user.js              # Pinia user store
    │   └── firebase.js                 # Firebase web config
    ├── vercel.json
    ├── vite.config.js
    └── tailwind.config.js
```

---

## Features

### For Children (Students)
- **Dashboard** — points, badges, skill progress, mood tracking
- **Quizzes** — auto-generated topic quizzes with AI explanations
- **Financial Literacy** — finance games, videos, and quizzes
- **Safety Skills** — safety comics and video lessons
- **Problem Solving** — AI-generated thought-provoking questions (beginner/medium/advanced)
- **Diary** — daily entries with AI mood analysis and scoring
- **RAG Chatbot** — child-friendly Q&A backed by a curated knowledge base + web search
- **Mentor Chatbot** — personalised AI mentor that reads diary entries and gives guidance
- **Voice Companion** — VAPI-powered voice interaction

### For Parents
- Register and link children via a one-time parent code
- View child progress, mood trends, badge history
- Manage emergency contacts

### For Admins
- Upload and manage quizzes, badges, safety content, finance videos, and comics
- Dashboard with skill engagement charts, mood trend graphs, and system alerts
- Manage all users

---

## User Roles

| Role | Description |
|---|---|
| `user` | Child aged 8–14, linked to a parent |
| `parent` | Oversees one or more children |
| `admin` | Full platform access, content management |

---

## Getting Started

### Prerequisites

- Python 3.13
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Ollama](https://ollama.com) running locally with `gemma4:31b-cloud` pulled
- Firebase project with Firestore and Email/Password auth enabled

### Clone the Repository

```bash
# Clone backend branch
git clone -b backend https://github.com/kohliaryan/soft-engg-project-may-2025-se-May-10.git backend

# Clone frontend branch
git clone -b frontend https://github.com/kohliaryan/soft-engg-project-may-2025-se-May-10.git frontend
```

---

### Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Copy and fill environment variables
cp .env.example .env   # or create .env manually (see below)

# Run development server
uv run uvicorn app.main:app --reload --port 8000
```

Visit **http://127.0.0.1:8000/docs** for interactive Swagger API docs.

---

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Visit **http://localhost:5173**

The frontend proxies `/api` requests to `http://127.0.0.1:8000` automatically in development (configured in `vite.config.js`).

---

## Environment Variables

Create `backend/.env` with the following:

```env
# ── Firebase (Service Account) ─────────────────────────────────────────────────
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# ── App ────────────────────────────────────────────────────────────────────────
APP_NAME=Life Skills World
DEBUG=True
ENVIRONMENT=development

# ── Ollama (AI) ────────────────────────────────────────────────────────────────
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma4:31b-cloud
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_API_KEY=                         # Leave empty for local Ollama

# ── External APIs ──────────────────────────────────────────────────────────────
GOOGLE_API_KEY=your-google-api-key      # Gemini (used by auto quiz generator)
PINECONE_API_KEY=your-pinecone-key
TAVILY_API_KEY=your-tavily-key
VAPI_API_KEY=your-vapi-key
VAPI_PUBLIC_KEY=your-vapi-public-key

# ── LangSmith (optional, for tracing) ─────────────────────────────────────────
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=appfirst
```

Create `frontend/.env.production`:

```env
VITE_API_BASE_URL=https://your-backend.onrender.com
VITE_FIREBASE_API_KEY=your-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

---

## API Reference

All endpoints are prefixed with `/api/v1`. Full interactive docs available at `/docs`.

| Group | Prefix | Description |
|---|---|---|
| Auth | `/api/v1/auth` | Register, login, refresh token, logout, password change |
| Users | `/api/v1/users` | Profile CRUD, badges, points, emergency contacts |
| Admin | `/api/v1/admin` | Content management, user management |
| Admin Dashboard | `/api/v1/admin-dashboard` | Stats, charts, alerts |
| Quiz | `/api/v1/quiz` | Quiz CRUD, attempts, auto-generation |
| Diary | `/api/v1/diary` | Diary entries with AI mood analysis |
| Finance | `/api/v1/finance` | Finance videos, games, quizzes |
| Safety | `/api/v1/safety` | Safety comics and videos |
| Skills | `/api/v1/skills` | Skill tracking and engagement |
| Mentor Chatbot | `/api/v1/mentor` | Session init, chat, history |
| RAG Chatbot | `/api/v1/rag` | Knowledge base + web search Q&A |
| Problem Solving | `/api/v1/problem-solving` | AI question generation |
| Parent | `/api/v1/parent` | Parent code generation, child linking |
| VAPI | `/api/v1/vapi` | Voice assistant integration |
| Public | `/api/v1/public` | Health check, public content |

### Auth Flow

```
1. Frontend → Firebase Auth (createUserWithEmailAndPassword)
2. Firebase Auth → returns ID token
3. Frontend → POST /api/v1/auth/complete-registration  { id_token, ...user_data }
4. Backend → verifies ID token → creates Firestore user doc → returns JWT
5. Frontend stores JWT → uses as Bearer token for all subsequent requests
```

---

## AI Features

### Mentor Chatbot
- Powered by Ollama `gemma4:31b-cloud` via LangGraph
- Reads the child's latest diary entry and past conversation summaries
- Maintains per-session context in SQLite (`mentor_app.db`)
- Age-aware responses (7–14 year olds)

### RAG Chatbot
- Routes questions to: RAG knowledge base, web search (Tavily), or direct LLM answer
- Uses Ollama `nomic-embed-text` for embeddings stored in Pinecone
- Filters out age-inappropriate web content
- Context window managed across sessions via SQLite (`rag_app.db`)

### Diary Summarizer
- Analyzes diary entries for mood score (1–10), themes, and suggestions
- Content validation filters gibberish entries
- Uses Ollama Cloud API directly via `requests`

### Problem Solving Generator
- LangGraph workflow generates unique MCQ questions for 3 difficulty levels
- Uniqueness tracking per user prevents repeated questions
- Emergency fallback question if LLM fails

### Auto Quiz Generator
- Generates topic-based quizzes using Google Gemini API
- Validates question quality before saving

---

## Deployment

### Backend — Render

**`backend/Dockerfile`**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Steps:**
1. [render.com](https://render.com) → New → Web Service
2. Connect GitHub repo, set Root Directory to `backend`, Branch to `backend`
3. Runtime: **Docker**
4. Add all environment variables from the `.env` section above
5. Deploy

### Frontend — Vercel

**`frontend/vercel.json`**
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Steps:**
1. [vercel.com](https://vercel.com) → New Project
2. Import GitHub repo, Root Directory: `frontend`, Branch: `frontend`
3. Framework: **Vite**
4. Add all `VITE_*` environment variables
5. Deploy

After deploying, add your Vercel URL to the backend CORS allowed origins in `app/main.py`.

---

## Scripts

### Create Admin User

```bash
cd backend
uv run python scripts/create_admin.py
```

### Check API Key Status

```bash
uv run check_keys.py
```

### Test Firebase Connection

```bash
uv run test_firebase.py
```

---

## Firestore Collections

| Collection | Description |
|---|---|
| `users` | All user documents (students, parents, admins) |
| `parent_codes` | One-time codes for child registration |
| `refresh_tokens` | JWT refresh token store |
| `quizzes` | Quiz content |
| `quiz_attempts` | Student quiz attempt records |
| `diary_entries` | Daily diary entries with AI analysis |
| `badges` | Badge definitions |
| `user_badges` | Badges earned by users |
| `skills` | Skill definitions |
| `skill_engagements` | Skill engagement tracking |
| `skill_stats` | Aggregated skill statistics |
| `game_items` | Finance game items |
| `game_levels` | Finance game levels |
| `daily_questions` | Problem solving question history |
| `problem_solving_progress` | Per-user problem solving progress |
| `questions` | Question bank |
| `question_options` | Answer options |
| `quizzes` | Quiz sets |
| `user_reactions` | Content reactions |
| `_health_check` | Firebase connection test (auto-created) |

---

## License

This project was built as part of the IIT Madras BS in Data Science — Software Engineering course (May 2025, Group SE-May-10).
