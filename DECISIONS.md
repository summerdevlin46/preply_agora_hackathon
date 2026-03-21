# Mirror — Architecture Decisions

## What is Mirror?
Mirror is a post-lesson AI speaking coach. A teacher uploads their worksheet, writes a brief lesson context, and Mirror generates a personalised Anam avatar session for the student to complete after class. The avatar conducts a live spoken exercise — correcting errors, asking follow-up questions, and scoring the student in real time.

---

## Key Decisions

### 1. Vision model for OCR (not Tesseract)
We use GPT-4o-mini with vision to parse uploaded worksheets into structured JSON rather than a traditional OCR library like Tesseract.

**Why:** Traditional OCR returns raw text with no understanding of structure. A vision model returns a clean JSON schema with title, topic, level, sections, items, and answer key — exactly what we need to generate a grounded avatar prompt. It also handles PDFs and images with no extra pipeline.

**Trade-off:** More expensive per parse, so we cache results keyed by file hash + model + prompt version.

---

### 2. Single GPT-4o call generates all four mode prompts
Rather than four separate API calls (one per exercise mode), we generate all four avatar prompts in a single structured JSON response.

**Why:** Reduces latency, keeps context consistent across modes, and makes regeneration of a single mode cheaper — we pass `existing_prompts` and only ask the model to revise one.

**Trade-off:** Larger single response, higher chance of JSON parse failure — mitigated by strict validation and error handling.

---

### 3. Narrative prompt format (not template sections)
Avatar prompts are single flowing director's scripts ("You are Leo... 1. Read the sentence... 2. Ask the student...") rather than structured PERSONALITY / GOAL / GUARDRAILS sections.

**Why:** Anam performs better with explicit numbered step instructions. A narrative format also makes regeneration feedback more targeted — a teacher can say "make step 3 harder" and the model knows exactly what to revise.

---

### 4. SQLite for prompt persistence
Generated avatar prompts are saved to SQLite under a `chat_id` key. The Next.js frontend fetches the prompt via `GET /api/chat/{chat_id}/instructions` before starting the Anam session.

**Why:** Simple, zero-dependency, works locally and in Docker. The schema already supports `completionState` so we can mark sessions as done once the student finishes — useful for the teacher debrief view.

**Long term:** Migrate to DynamoDB for scale (already planned in the original architecture).

---

### 5. Regeneration with feedback, not random retry
When a teacher is unhappy with a generated prompt, they type why (e.g. "make the errors harder") and hit Regenerate. This feedback is passed back to the cleanup model alongside the original inputs.

**Why:** Random retries produce random results. Targeted feedback produces targeted revisions. The `retry_count` is tracked per session — this is the seed for a future RL reward signal where teacher acceptance without regeneration = positive reward.

**Long term:** Multi-armed bandit (already scaffolded in `src/mirror/rl/`) selects prompt style configurations. Reward = teacher accepts without regenerating.

---

### 6. `src/` layout with editable install
All Python source lives in `src/mirror/` and is installed as an editable package via `pyproject.toml`. Tests import from `mirror.*` not from relative paths.

**Why:** Standard Python packaging convention — same reasoning as `src/` in C++/Rust projects. Prevents accidental imports from the project root and makes the package boundary explicit.

---

### 7. FastAPI + Next.js, not Gradio
We started with Gradio for rapid prototyping but switched to FastAPI + Next.js once the frontend requirements became clear.

**Why:** Gradio is excellent for internal demos but doesn't support the Anam avatar session flow, custom routing per `chat_id`, or the multi-panel teacher UI. FastAPI gives us a clean REST API the Next.js frontend can consume directly.

---

### 8. Error Detective as primary demo mode
Of the four exercise modes, Error Detective is the most structured and most robustly specified — 6 sentences, strict four-step loop, running score, final summary.

**Why:** It maps directly to the worksheet content (grammar error types), produces measurable output (score), and demonstrates the avatar's ability to wait, assess, and respond — the hardest Anam capabilities to showcase.

---

## What we'd build next (given more time)

- **RL reward signal** — log `(mode, retry_count, feedback)` to DynamoDB, train bandit on teacher acceptance rate
- **Student session report** — parse Anam transcript after session ends, send structured debrief to teacher
- **Thymia integration** — real-time speech confidence scoring during the session feeds back into difficulty selection ACTUALLY DONE thanks to the report
- **Multi-turn memory** — avatar remembers errors from earlier in the session when giving the final summary MUST SEE IF THIS IS A LIMITATION OF THE AVATARS
