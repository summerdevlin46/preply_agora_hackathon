# 🪞 Mirror — AI-Powered Post-Lesson Language Coach

> **Preply x Agora Hackathon** | AI Agents for NextGen Language Learning | Barcelona, March 2026

Mirror is a real-time, adaptive language learning agent that activates immediately after a Preply lesson. It listens to the live session, synthesizes teacher intent with AI-detected learner gaps, and delivers a personalized, timed, RL-driven exercise session through a conversational AI avatar.

---

## 🧠 Core Concept

Most language learning tools are disconnected from the actual lesson. Mirror closes the loop:

1. **Teacher sets intent** — uploads a worksheet, tags topics, leaves a voice note
2. **Mirror listens during the lesson** — Thymia analyzes speech confidence and fluency in real time
3. **Avatar coach activates post-lesson** — Anam delivers targeted exercises using the teacher's content
4. **RL engine adapts difficulty** — every response updates the learner's profile
5. **Teacher gets a debrief** — sees what stuck, what didn't, what to revisit next session

---

## 🏗️ Architecture Overview

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full technical deep-dive.

```
┌─────────────────────────────────────────────────────────────┐
│                     TEACHER INTERFACE                        │
│   Worksheet upload · Topic tags · Exercise prefs · Notes    │
└───────────────────────┬─────────────────────────────────────┘
                        │ Teacher Intent Package
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│         (OpenAI GPT-4o · LangChain agent framework)         │
│   Merges teacher intent + Thymia signal → exercise plan     │
└──────┬────────────────┬────────────────────┬────────────────┘
       │                │                    │
       ▼                ▼                    ▼
┌────────────┐  ┌──────────────┐  ┌─────────────────────┐
│   Thymia   │  │  RL Engine   │  │    Anam Avatar       │
│ Speech STT │  │ Bandit Model │  │  Exercise Delivery   │
│ Confidence │  │ Item Select  │  │  Hint Scaffolding    │
│  Scoring   │  │ Format Select│  │  Timer Management    │
└─────┬──────┘  └──────┬───────┘  └──────────┬──────────┘
      │                │                      │
      └────────────────┴──────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGORA REAL-TIME LAYER                      │
│         Audio streaming · Turn detection · Latency mgmt     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   PROGRESS DASHBOARD                         │
│     Fluency score · Hesitation map · Exercise results       │
│              Debrief summary → Teacher view                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Real-time audio/video | Agora RTC SDK |
| Speech analysis & scoring | Thymia API |
| LLM / reasoning | OpenAI GPT-4o |
| Agent orchestration | LangChain (Python) |
| AI avatar | Anam SDK |
| RL / adaptive difficulty | Custom multi-armed bandit (Python) |
| Backend | FastAPI (Python) |
| Frontend | React + TypeScript |
| Infrastructure | AWS (Lambda, S3, DynamoDB) |

---

## 📁 Repository Structure

```
mirror/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md        ← Full technical architecture
│   ├── API_REFERENCE.md       ← Partner API integration notes
│   └── DEMO_SCRIPT.md         ← Hackathon demo flow
├── backend/
│   ├── main.py                ← FastAPI entry point
│   ├── orchestrator/
│   │   ├── agent.py           ← LangChain orchestrator agent
│   │   └── prompts.py         ← System prompts for GPT-4o
│   ├── rl_engine/
│   │   ├── bandit.py          ← Multi-armed bandit implementation
│   │   ├── item_selector.py   ← Exercise item selection logic
│   │   └── learner_profile.py ← Per-learner state tracking
│   ├── integrations/
│   │   ├── thymia.py          ← Thymia API client
│   │   ├── agora.py           ← Agora RTC integration
│   │   ├── anam.py            ← Anam avatar client
│   │   └── openai_client.py   ← OpenAI wrapper
│   ├── teacher/
│   │   ├── worksheet_parser.py ← Parse uploaded worksheets
│   │   └── intent_builder.py   ← Build teacher intent package
│   └── models/
│       ├── session.py          ← Session data models
│       ├── exercise.py         ← Exercise types and schemas
│       └── learner.py          ← Learner profile schema
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TeacherPanel/   ← Worksheet upload, tags, notes
│   │   │   ├── AvatarSession/  ← Anam avatar + timer UI
│   │   │   └── Dashboard/      ← Progress visualization
│   │   ├── hooks/
│   │   │   ├── useAgora.ts     ← Agora audio hook
│   │   │   └── useSession.ts   ← Session state management
│   │   └── App.tsx
├── scripts/
│   ├── seed_exercises.py       ← Seed sample exercise bank
│   └── simulate_session.py     ← Simulate a lesson for demo
└── requirements.txt
```

---

## 👥 Team & Work Division

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Team Split section.

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/mirror.git
cd mirror

# Backend
pip install -r requirements.txt
cp .env.example .env   # add your API keys
uvicorn backend.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 🔑 Environment Variables

```
OPENAI_API_KEY=
AGORA_APP_ID=
AGORA_APP_CERTIFICATE=
THYMIA_API_KEY=
ANAM_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-west-1
```

---

## 🏆 Hackathon Challenge Tracks

Mirror addresses all three tracks:

- ✅ **Visualizing Learning Progress** — fluency scores, hesitation maps, session-over-session trends
- ✅ **Accelerating Learning with Agents** — RL-driven adaptive exercise engine with teacher-guided content
- ✅ **Live Learning & Real-Time Context** — Agora + Thymia pipeline listens to the actual lesson

---

## 📅 Hackathon

**Event:** Preply x Agora Hackathon — AI Agents for NextGen Language Learning  
**Date:** March 20–21, 2026  
**Location:** Preply Barcelona Office, Carrer de Badajoz 97
