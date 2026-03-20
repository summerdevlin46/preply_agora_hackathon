# Mirror — Technical Architecture

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Component Breakdown](#2-component-breakdown)
3. [Data Flow](#3-data-flow)
4. [RL Engine Design](#4-rl-engine-design)
5. [Exercise Types & Timer Logic](#5-exercise-types--timer-logic)
6. [Partner API Integration Notes](#6-partner-api-integration-notes)
7. [NLP Engineer Notes — Speech Systems Primer](#7-nlp-engineer-notes--speech-systems-primer)
8. [Team Split](#8-team-split)
9. [MVP Scope vs. Stretch Goals](#9-mvp-scope-vs-stretch-goals)
10. [Risk Register](#10-risk-register)

---

## 1. System Overview

Mirror operates in three temporal phases:

```
PHASE 1: PRE/POST-LESSON (Teacher)
  Teacher uploads worksheet → tags topics → sets exercise preferences → leaves voice/text note
  → Worksheet parser extracts vocabulary, grammar rules, prompts
  → Intent Builder packages this into a structured TeacherIntentPackage

PHASE 2: DURING LESSON (Background, optional)
  Agora streams live audio → Thymia analyzes in real time
  → ThymiaSignal produced: fluency score, hesitation map, error flags, confidence level

PHASE 3: POST-LESSON (Student)
  Orchestrator merges TeacherIntentPackage + ThymiaSignal
  → RL engine builds ordered exercise queue
  → Anam avatar delivers exercises with timer
  → Student responds via mic (Agora) → Thymia scores response
  → RL reward signal updates learner profile
  → Session debrief sent to teacher
```

---

## 2. Component Breakdown

### 2.1 Teacher Interface (Frontend)

A lightweight React panel accessible after each lesson.

**Inputs:**
- Worksheet upload (PDF, DOCX, or image) — parsed server-side
- Topic tags (free text or from a preset taxonomy: vocab, conjugation, pronunciation, writing, speaking, reading)
- Exercise type preferences (checkboxes: vocab drill, conjugation, speaking, writing)
- Time limit per exercise (slider: 3s–60s) and total session length (5/10/15/20 min)
- Voice note (recorded via browser mic, transcribed by Thymia/Whisper) or text note

**Output:** `TeacherIntentPackage` (JSON) sent to backend

```json
{
  "session_id": "abc123",
  "learner_id": "xyz789",
  "topics_covered": ["subjunctive mood", "restaurant vocabulary"],
  "exercise_types": ["conjugation", "vocab_drill", "speaking"],
  "time_limit_per_exercise_s": 8,
  "total_session_duration_s": 900,
  "worksheet_items": [
    {"type": "vocab", "term": "el camarero", "definition": "the waiter", "example": "El camarero nos trajo la carta."},
    {"type": "conjugation", "verb": "querer", "tense": "subjunctive", "target_forms": ["quiera", "quieras", "quiera"]}
  ],
  "teacher_note": "She kept confusing ser vs estar. Focus conjugation there first.",
  "pressure_profile": "medium"
}
```

---

### 2.2 Worksheet Parser (`backend/teacher/worksheet_parser.py`)

Handles: PDF, DOCX, image (via OCR).

**Pipeline:**
1. File type detection
2. Text extraction (PyMuPDF for PDF, python-docx for DOCX, Tesseract for images)
3. GPT-4o structured extraction — prompt asks it to identify vocab items, grammar rules, exercise prompts, and return structured JSON
4. Returns `ParsedWorksheet` object

**Key prompt pattern:**
```
You are a language teaching assistant. Extract all learnable items from this worksheet.
Return ONLY valid JSON with this schema: { vocab: [...], grammar_rules: [...], prompts: [...] }
Do not include any explanation.
```

---

### 2.3 Thymia Integration (`backend/integrations/thymia.py`)

Thymia is a cognitive and voice biomarker company. Their API analyzes speech for:
- Fluency (words per minute, pause rate)
- Hesitation markers (filled pauses: "um", "uh", false starts)
- Confidence proxies (pitch variance, speech rate consistency)
- Accuracy flags (when combined with expected output)

**Two usage modes:**

**Mode A — Live lesson monitoring (stretch goal):**
Stream audio from the Agora channel → Thymia processes in chunks → accumulates `ThymiaSignal`

**Mode B — Exercise scoring (MVP):**
After student responds to an exercise, send the audio clip → Thymia returns a score for that specific response

For the hackathon, **prioritize Mode B** — it's simpler to integrate and directly powers the RL reward signal.

```python
# Simplified Thymia client
class ThymiaClient:
    def score_response(self, audio_bytes: bytes, expected: str) -> dict:
        # POST to Thymia API
        # Returns: { fluency_score, hesitation_count, confidence, wpm }
        pass
    
    def get_session_signal(self, session_audio: bytes) -> dict:
        # Batch analysis of full lesson audio
        # Returns: { weak_topics, strong_topics, overall_confidence }
        pass
```

---

### 2.4 Orchestrator Agent (`backend/orchestrator/agent.py`)

The brain of Mirror. A LangChain agent powered by GPT-4o.

**Inputs:**
- `TeacherIntentPackage`
- `ThymiaSignal` (if available from live lesson) or learner profile history
- Learner's historical RL state (`LearnerProfile`)

**Responsibilities:**
1. Merge and prioritize — teacher note overrides AI inference; Thymia signal refines ordering
2. Generate exercise instances from worksheet items (e.g., turn a vocab item into a fill-in-the-blank, a spoken prompt, or a multiple choice question)
3. Generate hint text for each exercise (scaffolded, revealed only after timeout)
4. Produce an ordered `ExerciseQueue` for the RL engine to work from
5. Generate the avatar's opening greeting (personalized, references the specific lesson)

**Tools available to the agent:**
- `generate_exercise(item, format_type)` — creates a specific exercise instance
- `generate_hint(exercise)` — creates the scaffolded hint
- `get_learner_history(learner_id)` — fetches past weak spots from DynamoDB
- `build_greeting(teacher_note, thymia_signal, learner_name)` — creates avatar opening line

---

### 2.5 RL Engine (`backend/rl_engine/`)

A contextual multi-armed bandit. No external RL library needed — implemented from scratch in ~150 lines.

#### State
Per learner, per item, we track:
```python
@dataclass
class ItemState:
    item_id: str
    attempts: int = 0
    successes: int = 0
    avg_response_time_ratio: float = 1.0  # actual_time / time_limit (lower = better)
    last_seen: datetime = None
    preferred_format: str = None          # learned over time
    difficulty_level: int = 1             # 1-5
```

#### Reward Signal
After each exercise response, compute reward:

```python
def compute_reward(response: ExerciseResponse) -> float:
    score = 0.0
    
    # Correctness (0.0–0.5)
    score += 0.5 * response.thymia_score.accuracy
    
    # Speed relative to time limit (0.0–0.3)
    time_ratio = response.response_time_s / response.time_limit_s
    score += 0.3 * max(0, 1 - time_ratio)
    
    # Fluency bonus (0.0–0.2)
    score += 0.2 * response.thymia_score.fluency_score
    
    return score  # 0.0–1.0
```

#### Item Selection (UCB1 algorithm)
Upper Confidence Bound — balances exploiting known weak spots with exploring items not yet seen:

```python
def select_next_item(items: list[ItemState], t: int) -> ItemState:
    scores = []
    for item in items:
        if item.attempts == 0:
            return item  # always try unseen items first
        exploitation = item.successes / item.attempts
        exploration = math.sqrt(2 * math.log(t) / item.attempts)
        scores.append(exploitation + exploration)
    return items[argmax(scores)]
```

#### Format Selection
Separate bandit per learner that learns which format works best for them:
- `vocab_drill` → flashcard-style: "What does 'el camarero' mean?"
- `conjugation` → fill-in: "Conjugate 'querer' in subjunctive for 'ella'"
- `speaking` → open prompt: "Use 'quiera' in a sentence about the restaurant"
- `writing` → typed response (no timer pressure, focus on accuracy)

#### Difficulty Escalation
```python
def update_difficulty(item: ItemState, reward: float):
    if reward > 0.85 and item.difficulty_level < 5:
        item.difficulty_level += 1
        item.time_limit_s = max(3, item.time_limit_s - 2)  # tighten timer
    elif reward < 0.4 and item.difficulty_level > 1:
        item.difficulty_level -= 1
        item.time_limit_s = min(60, item.time_limit_s + 3)  # loosen timer
```

---

### 2.6 Anam Avatar (`backend/integrations/anam.py`)

Anam provides photorealistic AI avatars that speak via TTS and listen via STT.

**What Mirror uses Anam for:**
- Opening greeting (personalized by orchestrator)
- Exercise delivery (reading out the question)
- Hint delivery (after timeout, avatar says the hint naturally)
- Encouragement / transition phrases between exercises
- Session wrap-up summary

**Key integration pattern:**
```python
class AnamClient:
    def speak(self, text: str, emotion: str = "encouraging"):
        # POST to Anam API with script text
        # Anam streams the avatar video back
        pass
    
    def listen(self, timeout_s: int) -> AudioStream:
        # Open mic via Agora, pass audio to Thymia for scoring
        pass
```

**Emotion states used:** `encouraging`, `neutral`, `celebratory`, `patient`

Mirror uses `patient` when delivering hints (avatar leans in slightly, slower pace), `celebratory` on streaks of correct answers, and `encouraging` as the default.

---

### 2.7 Agora Real-Time Layer (`backend/integrations/agora.py`)

Agora handles all audio streaming — both during the lesson (if Mode A Thymia is enabled) and during the exercise session (student responses).

**For NLP engineers unfamiliar with Agora:** Think of it as the plumbing. You join a channel, publish your mic audio, subscribe to remote audio. The SDK handles latency, packet loss, and codec negotiation. You mostly interact with callbacks.

**Key concepts:**
- `RtcEngine` — main Agora object, one per session
- `Channel` — a named room, teacher + learner + Mirror all join the same channel
- `AudioFrame` — raw PCM audio data, what you pass to Thymia

```python
# Simplified Agora usage
engine = AgoraRtcEngine(app_id=AGORA_APP_ID)
engine.join_channel(token, channel_name, uid=MIRROR_BOT_UID)

@engine.on("audio_frame")
def on_audio_frame(frame: AudioFrame):
    # Pass to Thymia in chunks
    thymia_buffer.append(frame.pcm_data)
```

**For the hackathon:** Use the Agora Web SDK (JavaScript) on the frontend for the student mic. Use the backend SDK only if doing live lesson monitoring. For MVP, student responses are captured browser-side and sent as audio blobs to the backend.

---

### 2.8 Progress Dashboard (Frontend)

A simple React component shown after the exercise session ends.

**Displays:**
- Overall fluency score (this session vs. last session)
- Hesitation heatmap by topic (which topics caused the most pauses)
- Exercise-by-exercise results (correct/incorrect, response time vs. limit)
- Items flagged for next lesson ("Still needs work: subjunctive of *querer*")

**Teacher view (same data, different framing):**
- Which exercises were completed
- Where the student struggled post-lesson vs. during the lesson
- Suggested focus for next session (generated by GPT-4o)

---

## 3. Data Flow

```
[Teacher uploads worksheet]
         │
         ▼
[worksheet_parser.py] ──GPT-4o──► ParsedWorksheet (JSON)
         │
         ▼
[intent_builder.py] ──────────► TeacherIntentPackage (JSON)
         │
         │         [Agora live audio during lesson]
         │                    │
         │                    ▼
         │          [Thymia Mode A analysis]
         │                    │
         ▼                    ▼
[orchestrator/agent.py] ◄─── ThymiaSignal + LearnerProfile
         │
         ▼
[ExerciseQueue] ──────────────► [RL Engine: item + format selection]
                                          │
                                          ▼
                               [Anam avatar speaks exercise]
                                          │
                                          ▼
                               [Student responds via Agora mic]
                                          │
                                          ▼
                               [Thymia Mode B: score response]
                                          │
                                          ▼
                               [RL reward computed → LearnerProfile updated]
                                          │
                              ┌───────────┴────────────┐
                              ▼                        ▼
                    [Next exercise selected]   [Session ends → Dashboard]
                                                        │
                                                        ▼
                                             [Teacher debrief sent]
```

---

## 4. RL Engine Design

### Why a bandit and not full RL?

Full reinforcement learning (e.g., PPO, Q-learning) requires many episodes to converge and is hard to debug in 18 hours. A **multi-armed bandit** gives you:
- Principled exploration vs. exploitation
- Fast convergence per-item (tens of attempts, not thousands)
- Fully interpretable — you can log exactly why an item was selected
- Honest to call "RL" in the pitch, because it is

### The two bandits

**Bandit 1 — Item selection (UCB1)**
Decides *which* exercise item to show next. Tracks success rate and recency per item.

**Bandit 2 — Format selection (Thompson Sampling)**
Decides *how* to present the item (vocab drill vs. speaking vs. writing). Uses Beta distribution per format per learner — updates as evidence accumulates.

```python
# Thompson Sampling for format selection
def select_format(learner: LearnerProfile, item: ItemState) -> str:
    formats = ["vocab_drill", "conjugation", "speaking", "writing"]
    samples = []
    for fmt in formats:
        alpha = learner.format_successes[fmt] + 1
        beta = learner.format_failures[fmt] + 1
        samples.append(np.random.beta(alpha, beta))
    return formats[argmax(samples)]
```

### Spaced repetition layer

On top of the bandit, items the student mastered (reward > 0.85 for 3 consecutive attempts) are **retired** from the current session and scheduled for re-appearance after a delay (next session, or 2 sessions later). Items that were failed are **re-queued** within the current session in a different format.

---

## 5. Exercise Types & Timer Logic

| Type | Description | Default Timer | Hint Trigger | Difficulty Axis |
|---|---|---|---|---|
| `vocab_drill` | "What does X mean?" | 5s | 3s | add distractors, reverse direction |
| `conjugation` | "Conjugate X for ella" | 8s | 5s | add irregular verbs, compound tenses |
| `speaking` | "Use X in a sentence" | 15s | 10s | constrain topic, require specific structure |
| `writing` | "Write a sentence using X" | 45s | 30s | require paragraph, add constraints |
| `multiple_choice` | 4 options, tap to answer | 6s | none | increase distractor similarity |

**Timer behavior:**
- Countdown shown visually in the UI (circular progress ring around avatar)
- At 50% of timer: subtle visual pulse (urgency signal)
- At timeout: avatar delivers hint naturally in speech, then waits another half-cycle
- At second timeout: avatar reveals answer, marks as failed, moves on

---

## 6. Partner API Integration Notes

### Agora
- Docs: https://docs.agora.io
- Use Web SDK (agora-rtc-sdk-ng) for browser mic capture
- Token generation requires your App Certificate (server-side only — never expose)
- Key classes: `AgoraRTC.createClient()`, `createMicrophoneAudioTrack()`
- Audio frames for Thymia: use `getMediaStreamTrack()` → MediaRecorder → Blob

### Thymia
- Contact Thymia team at hackathon for API credentials and endpoint docs
- Expected: REST API, audio file upload or streaming endpoint
- Fallback if unavailable: use OpenAI Whisper for transcription + GPT-4o for fluency proxy scoring

### Anam
- Docs: https://docs.anam.ai
- Key concept: "Persona" — a configured avatar with voice, appearance, system prompt
- Create a Mirror persona with a warm, patient tutor personality
- `anam.streamMessage(text)` → avatar speaks; `anam.on('userSpeech', cb)` → captures student

### OpenAI
- Use `gpt-4o` for orchestration, worksheet parsing, debrief generation
- Use structured outputs (`response_format: { type: "json_object" }`) for all parsing tasks
- Use `gpt-4o-mini` for hint generation (lower latency, lower cost)
- Whisper API as Thymia fallback for transcription

### AWS
- DynamoDB: learner profiles, session history, item states
- S3: worksheet file storage, session audio (if recording)
- Lambda: optional for async debrief generation
- For hackathon: run everything locally, use DynamoDB only for learner profile persistence

---

## 7. NLP Engineer Notes — Speech Systems Primer

Since the team is NLP-focused rather than speech systems-focused, here's what you need to know to avoid blockers.

### Audio formats
- Agora captures raw PCM (16kHz, 16-bit, mono is fine for speech)
- Thymia and Whisper both accept WAV or MP3
- Convert PCM → WAV server-side: `soundfile` or `scipy.io.wavfile`
- Browser MediaRecorder outputs WebM/Opus — convert with `pydub` or `ffmpeg`

### Latency expectations
- Agora → browser: ~100–200ms (fine, it's designed for this)
- Thymia response scoring: unclear — **ask at hackathon**, assume 500ms–2s
- Anam avatar speaking latency: ~300–500ms from API call to first frame
- OpenAI GPT-4o: ~800ms–2s for typical prompts
- **Design the UX to hide latency:** avatar has "thinking" animations, timer pauses while scoring

### What Thymia actually measures
Thymia is a cognitive biomarker company. Their core tech comes from mental health screening — detecting depression, anxiety, and cognitive decline from voice patterns. For language learning, the useful signals are:
- **Speech rate** (words per minute) — proxy for fluency
- **Pause rate and duration** — hesitation signal
- **Pitch variance** — confidence proxy
- **Articulation rate** — pronunciation fluency (excluding pauses)

You don't need to understand the underlying DSP. Treat it as a black box that returns a structured JSON of scores. If their API is hard to integrate in the time available, **fall back to Whisper + GPT-4o** for a reasonable proxy.

### Whisper fallback pattern
```python
import openai

def score_response_fallback(audio_bytes: bytes, expected_answer: str) -> dict:
    transcript = openai.audio.transcriptions.create(
        model="whisper-1",
        file=("response.wav", audio_bytes, "audio/wav")
    ).text
    
    score = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Expected: '{expected_answer}'\nStudent said: '{transcript}'\n"
                       f"Rate correctness 0.0-1.0 and fluency 0.0-1.0. Return JSON only."
        }],
        response_format={"type": "json_object"}
    )
    return json.loads(score.choices[0].message.content)
```

---

## 8. Team Split

The team has 3 NLP engineers. Suggested division:

### Engineer 1 — Orchestration & LLM Layer
**Files:** `backend/orchestrator/`, `backend/teacher/`, `backend/models/`

- Worksheet parser (GPT-4o structured extraction)
- Teacher intent builder
- LangChain orchestrator agent
- Exercise generation prompts
- Debrief summary generation
- OpenAI client wrapper

**Why this person:** Heaviest prompt engineering work. Pure NLP, no speech systems.

---

### Engineer 2 — RL Engine & Session Logic
**Files:** `backend/rl_engine/`, `backend/main.py` (API routes)

- Multi-armed bandit implementation (UCB1 + Thompson Sampling)
- Item state tracking and updates
- Spaced repetition scheduler
- Reward signal computation
- FastAPI routes connecting all components
- DynamoDB integration for learner profiles

**Why this person:** Algorithmic work, pure Python, no external API complexity.

---

### Engineer 3 — Integrations & Frontend
**Files:** `backend/integrations/`, `frontend/`

- Agora Web SDK integration (browser mic capture)
- Thymia API client (+ Whisper fallback)
- Anam avatar integration
- React frontend: Teacher panel, Avatar session UI, Progress dashboard
- Timer UI components
- Audio blob → backend pipeline

**Why this person:** Most API surface area, but Agora/Anam are well-documented SDKs. The frontend is minimal — 3 views, not a full app.

---

### Shared responsibility
- **Demo script** (`docs/DEMO_SCRIPT.md`) — all three, write it early
- **`scripts/simulate_session.py`** — mock a lesson so demo doesn't depend on a live tutor
- **Integration testing** — last 2 hours Saturday morning before presentations

---

## 9. MVP Scope vs. Stretch Goals

### MVP (must have for demo)
- [ ] Teacher panel: worksheet upload + topic tags + exercise type selection + time limit
- [ ] Worksheet parser: PDF/DOCX → structured exercise items via GPT-4o
- [ ] Exercise session: Anam avatar delivers exercises with countdown timer
- [ ] Student mic response via Agora → scored by Thymia (or Whisper fallback)
- [ ] RL engine: UCB1 item selection, basic reward signal, difficulty update
- [ ] Session debrief: simple dashboard showing results
- [ ] Teacher debrief: which items passed/failed

### Stretch goals (if time allows)
- [ ] Live lesson monitoring (Thymia Mode A during actual Agora lesson)
- [ ] Format selection bandit (Thompson Sampling per learner)
- [ ] Spaced repetition across multiple sessions
- [ ] Voice note from teacher (transcribed and parsed into intent)
- [ ] Emotion-aware avatar states (celebratory on streaks)
- [ ] Multi-language support (prompt engineering only)

---

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Thymia API hard to integrate | Medium | High | Whisper + GPT-4o fallback ready from hour 1 |
| Anam avatar latency too high | Low | Medium | Pre-record avatar lines for demo if needed |
| Agora browser mic not working | Low | High | Fall back to browser MediaRecorder API directly |
| OpenAI rate limits | Low | Medium | Cache exercise generation, use gpt-4o-mini for hints |
| Worksheet parser fails on complex formats | Medium | Low | Pre-parse 3 demo worksheets manually as JSON fixtures |
| RL engine over-engineered | Medium | Medium | Ship UCB1 only — Thompson Sampling is a stretch goal |
| Demo internet connectivity | Medium | High | Pre-record a full demo video as backup |

---

## Demo Script

See [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for the full 3-minute pitch flow.

**The golden path:**
1. Teacher uploads a worksheet (pre-loaded fixture) + leaves a voice note
2. System parses it — show the structured JSON output
3. Avatar activates: "Hi Ana, great lesson today. You worked on subjunctive mood — let's lock it in."
4. Vocab drill — student answers, Thymia scores, RL selects next
5. Conjugation exercise — student hesitates, timer runs out, avatar gives hint
6. Speaking exercise — student responds, avatar celebrates
7. Dashboard appears: fluency score, hesitation map, 2 items flagged for next lesson
8. Teacher view: "Ana completed 8/10 exercises. 'querer' subjunctive still needs work."
