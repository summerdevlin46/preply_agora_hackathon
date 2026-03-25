# AfterClass

AfterClass makes homework generation easy for teachers and delivers more targeted, personalised speaking practice to students.

Teachers upload their lesson materials (worksheets), add a prompt with context, and choose an exercise type (conversation, vocabulary, dictation, error detective). AfterClass generates an Anam avatar session with clear instructions for the avatar and a student activity page. When the student finishes, the teacher receives a report with performance insights, what the student got wrong, and suggestions for the next lesson — enriched with Thymia Helios statistics (confidence, frustration, etc.).

**Built at:** Preply × Agora Hackathon, Barcelona, March 2026

---

## What it does

1. **Teacher uploads materials** — worksheet is parsed via GPT-4o vision into structured JSON
2. **Teacher adds context + selects an exercise type** — conversation / vocabulary / dictation / error detective
3. **AfterClass generates the session** — Anam avatar instructions + student-facing task content
4. **Student completes the exercise** — live spoken practice with the avatar
5. **Teacher receives a report** — mistakes + suggested next-lesson topics, plus Thymia Helios voice/emotion biomarker stats (confidence, frustration, etc.)

---

## Architecture

```
Teacher uploads worksheet + prompt + selects exercise type
        ↓
POST /api/worksheet/parse      (GPT-4o vision → structured JSON)
        ↓
POST /api/exercises/generate   (GPT-4o → avatar prompt + student task per mode)
        ↓
Saved to SQLite under chat_id per mode
        ↓
Student opens /chat/{chat_id}
        ↓
GET /api/chat/{chat_id}/instructions → avatar system prompt
        ↓
POST /api/anam/session → Anam session token
        ↓
Live avatar session (voice + text)
        ↓
POST /api/chat/{chat_id}/complete     (transcript → teacher-facing feedback)
POST /api/report/analyze              (WAV → Thymia Helios → confidence/frustration/etc.)
        ↓
GET /api/report/{chat_id}/teacher     (merged teacher report)
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (TypeScript) |
| Backend | FastAPI (Python 3.13) |
| Worksheet parsing | GPT-4o vision |
| Avatar | Anam SDK |
| Voice / emotion biomarkers | Thymia (Helios) |
| LLM | OpenAI GPT-4o via `responses.create` |
| Agent orchestration | LangGraph |
| Storage | SQLite (local) |
| Package manager | uv |

---

## Quickstart

### Requirements

- Python 3.13+
- Node.js 18+
- `uv` — https://github.com/astral-sh/uv

### 1. Clone and install

```bash
git clone https://github.com/summerdevlin46/preply_agora_hackathon.git
cd preply_agora_hackathon
make setup
```

### 2. Environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-...
ANAM_API_KEY=...
ANAM_AVATAR_ID=...
ANAM_VOICE_ID=...
ANAM_LLM_ID=...
THYMIA_API_KEY=...

# Optional overrides
OPENAI_OCR_MODEL=gpt-4o-mini          # model for worksheet parsing
MIRROR_MODEL_BACKEND=openai           # openai | huggingface | local_oss
MIRROR_CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Run the backend

```bash
uv run uvicorn src.app:app --reload --port 8000
```

Check it's alive:

```bash
curl http://localhost:8000/api/health
```

### 4. Run the frontend

```bash
cd public
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`.

---

## Exercise modes

| Mode | Key | What happens |
|---|---|---|
| Conversation | `avatar_conversation` | Open spoken dialogue on the lesson topic |
| Vocabulary | `vocabulary_challenge` | Targeted vocabulary practice |
| Dictation | `read_aloud_review` | Listening + transcription / read-aloud feedback |
| Error Detective | `error_detective` | Student finds and fixes mistakes, explains rules |

---

## What’s next

- **Homework Wrapped (monthly)** — student-facing recap of progress and stats over time
- **More granular teacher analytics** — drilldown by skill/category
- **Adaptive difficulty** — adjust tasks live using Thymia Helios signals
