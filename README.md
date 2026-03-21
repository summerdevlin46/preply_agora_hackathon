# 🪞 Mirror — AI-Powered Post-Lesson Language Coach

Mirror turns a teacher's worksheet into a live AI avatar session for the student. The teacher uploads a PDF, adds lesson context, and Mirror generates a personalised speaking exercise delivered by an Anam AI avatar in real time.

**Built at:** Preply × Agora Hackathon, Barcelona, March 2026

---

## What it does

1. **Teacher uploads a worksheet** — Mirror parses it via GPT-4o vision OCR into structured JSON
2. **Teacher adds lesson context** — level, focus areas, any extra notes
3. **Mirror generates four avatar session prompts** — one per exercise mode (conversation, vocabulary, dictation, error detective)
4. **Student launches a live Anam session** — the avatar coaches them through the exercise by voice
5. **After the session** — Thymia Helios analyses the student's audio for confidence and fluency scores, GPT-4o generates a teacher report

---

## Architecture

```
Teacher uploads PDF
        ↓
POST /api/worksheet/parse   (GPT-4o vision OCR → structured JSON)
        ↓
POST /api/exercises/generate  (GPT-4o → 4 avatar prompts + tasks per mode)
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
POST /api/chat/{chat_id}/complete  (transcript → GPT-4o → teacher analysis)
POST /api/report/analyze           (WAV → Thymia Helios → confidence + fluency)
        ↓
GET /api/report/{chat_id}/teacher  (merged teacher report)
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (TypeScript) |
| Backend | FastAPI (Python 3.13) |
| OCR | GPT-4o vision |
| Avatar | Anam SDK |
| Voice biomarkers | Thymia Sentinel (Helios) |
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
git clone https://github.com/your-org/mirror.git
cd mirror
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
OPENAI_OCR_MODEL=gpt-4o-mini        # model for worksheet OCR
MIRROR_MODEL_BACKEND=openai          # openai | huggingface | local_oss
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

## API reference

### Worksheet

```
POST /api/worksheet/parse
  multipart: file (PDF, PNG, JPG)
  → { filename, worksheet_json, worksheet_text }
```

### Exercise generation

```
POST /api/exercises/generate
  JSON: {
    learner_name: str,
    topic: str,
    worksheet_json: dict,       # from /worksheet/parse
    teacher_notes: str,
    assignment_type: str,       # avatar_conversation | vocabulary_challenge | read_aloud_review | error_detective
    feedback: str,              # optional — for regeneration
    mode: str,                  # optional — which mode to regenerate
    existing_prompts: dict,     # optional — preserve other modes on regen
    retry_count: int,
    chat_id: str                # optional — provide to reuse session
  }
  → {
    chat_ids: { mode: chat_id },
    avatar_prompts: { mode: prompt },
    tasks: { mode: [{ title, description }] },
    learner_name, topic
  }
```

### Avatar session (Next.js API route)

```
POST /api/anam/session
  JSON: { instructions: str }
  → { sessionToken: str }
```

### Chat instructions (fetched by Next.js before Anam session)

```
GET /api/chat/get-user-chat-instructions
  → { instructions: str }

GET /api/chat/{chat_id}/instructions
  → { instructions: str }
```

### Session completion + report

```
POST /api/chat/{chat_id}/complete
  JSON: { messages: [{ role, content, interrupted }] }
  → { analysis: str }

POST /api/report/analyze
  multipart: chat_id, transcript (optional), wav_file
  → { chat_id, confidence_score, fluency_score, transcript, analysis }

GET /api/report/{chat_id}/teacher
  → { chat_id, confidence_score, fluency_score, transcript, analysis }
```

---

## Exercise modes

| Mode | Key | Avatar | What happens |
|---|---|---|---|
| Avatar Conversation | `avatar_conversation` | Sofia | Open spoken dialogue on lesson topic |
| Vocabulary Challenge | `vocabulary_challenge` | Max | Avatar gives definitions, student produces words |
| Read-Aloud Review | `read_aloud_review` | Priya | Student reads writing aloud, avatar gives feedback |
| Error Detective | `error_detective` | Leo | Avatar reads sentences with deliberate errors, student corrects and explains the rule |

**Error Detective is the primary demo mode** — 6 sentences, strict four-step loop, running score, final summary.

---

## Testing

```bash
make test
```

All tests run offline (mocked API calls) except the end-to-end workflow test which requires `OPENAI_API_KEY` and is skipped by default.

---

## Sharing publicly (demo day)

Run both servers, then expose with ngrok:

```bash
# Terminal 1
uv run uvicorn src.app:app --reload --port 8000

# Terminal 2
cd public && npm run dev

# Terminal 3 — expose backend
ngrok http 8000
# copy the https URL, set as NEXT_PUBLIC_API_BASE_URL in public/.env.local

# Terminal 4 — expose frontend
ngrok http 3000
# share this URL with judges
```

---

## Branch structure

| Branch | Purpose |
|---|---|
| `main` | Stable only |
| `dev` | Active integration work |
| `feature/*` | Individual features |

---

## What's next (post-hackathon)

- RL reward signal — log `(mode, retry_count, feedback)` to DynamoDB, train bandit on teacher acceptance rate
- Student session report — separate student-facing view from teacher report
- Thymia integration on real Anam audio — currently tested with synthetic WAV
- Vercel + AWS deployment — `Dockerfile` is ready
- Streaming responses for faster avatar prompt generation
- Multi-session memory — avatar remembers errors from previous sessions
