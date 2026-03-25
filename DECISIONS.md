# AfterClass — Architecture Decisions

## What is AfterClass?
AfterClass is an AI-powered homework generator and post-class speaking coach for language teachers and students.

A teacher uploads their lesson materials (e.g., class worksheets), adds brief context/instructions, and selects an exercise type:

- Conversation
- Vocabulary
- Dictation
- Error Detective

AfterClass generates:
- a personalised Anam avatar session (who the avatar is + what it will do)
- a student activity page for the chosen exercise

After the student completes the session, AfterClass produces a teacher-facing report summarizing performance, mistakes, and suggested next-lesson focus areas. The report includes voice and emotion biomarker statistics from Thymia Helios (e.g., confidence, frustration, etc.).

---

## Key Decisions

### 1. Privacy-first evaluation outside live lessons
We designed AfterClass to run speaking practice and speech analytics in a homework context rather than relying on recording live classroom sessions.

**Why:** Many students don’t consent to being recorded during lessons, and live sessions can include sensitive/personal topics. By moving measurement to a dedicated homework exercise, students can opt in with clearer consent and we can collect Thymia Helios signals (confidence, frustration, etc.) in a more controlled, exercise-only environment.

**Trade-off:** We lose some “in-class” realism, but gain higher consentability, clearer context, and more consistent data for reporting.

---

### 2. Vision model for worksheet parsing (not traditional OCR)
We use GPT-4o-mini with vision to parse uploaded worksheets into structured JSON rather than a traditional OCR library like Tesseract.

**Why:** Traditional OCR returns raw text with no understanding of structure. A vision model can return a clean schema (title, topic, level, sections, items, and answer key) that we can directly ground exercise generation on. It also handles PDFs and images without an extra pipeline.

**Trade-off:** More expensive per parse, so we cache results keyed by file hash + model + prompt version.

---

### 3. Single LLM call generates all four exercise-mode prompts
Rather than four separate API calls (one per exercise mode), we generate all four avatar prompts (conversation, vocabulary, dictation, error detective) in a single structured JSON response.

**Why:** Reduces latency, keeps context consistent across modes, and makes regeneration of a single mode cheaper — we pass `existing_prompts` and only ask the model to revise one.

**Trade-off:** Larger single response, higher chance of JSON parse failure — mitigated by strict validation and error handling.

---

### 4. Narrative prompt format for the Anam avatar (not template sections)
Avatar prompts are single flowing director scripts ("You are Leo... 1. Read the sentence... 2. Ask the student...") rather than structured PERSONALITY / GOAL / GUARDRAILS sections.

**Why:** Anam performs better with explicit numbered step instructions. Narrative prompts also make teacher feedback more actionable — e.g. “make step 3 harder.”

---

### 5. SQLite for prompt persistence (chat_id keyed)
Generated avatar prompts are saved to SQLite under a `chat_id` key. The Next.js frontend fetches the prompt via `GET /api/chat/{chat_id}/instructions` before starting the Anam session.

**Why:** Simple, zero-dependency, works locally and in Docker. The schema supports `completionState` so we can mark sessions as done once the student finishes — useful for teacher reporting.

**Long term:** Migrate to DynamoDB for scale.

---

### 6. Regeneration uses teacher feedback (not random retry)
When a teacher is unhappy with a generated prompt, they describe why (e.g. “make the errors harder”) and hit Regenerate. This feedback is passed back to the model alongside the original inputs.

**Why:** Random retries produce random results. Targeted feedback produces targeted revisions. We track `retry_count` per session as a seed for a future RL reward signal where teacher acceptance without regeneration = positive reward.

**Long term:** A multi-armed bandit (scaffolded in `src/mirror/rl/`) can select prompt-style configurations. Reward = teacher accepts without regenerating.

---

### 7. `src/` layout with editable install
All Python source lives in `src/mirror/` and is installed as an editable package via `pyproject.toml`. Tests import from `mirror.*` (not relative paths).

**Why:** Standard Python packaging convention. Prevents accidental imports from the project root and makes the package boundary explicit.

---

### 8. FastAPI + Next.js, not Gradio
We started with Gradio for rapid prototyping but switched to FastAPI + Next.js once the teacher + student flows became clear.

**Why:** Gradio is great for internal demos but doesn’t support the Anam avatar session flow, custom routing per `chat_id`, or the multi-panel teacher UI. FastAPI provides a clean REST API that the Next.js frontend can consume.

---

### 9. Error Detective as primary demo mode
Of the four exercise modes, Error Detective is the most structured and robustly specified — 6 sentences, strict four-step loop, running score, final summary.

**Why:** It maps directly to worksheet content (grammar error types), produces measurable output (score), and demonstrates the avatar’s ability to wait, assess, and respond — the hardest Anam capabilities to showcase.

---

## What we’d build next (given more time)

- **Teacher report improvements** — richer skill breakdowns, clearer “next lesson” recommendations
- **Real-time adaptation** — use Thymia Helios signals (confidence/frustration) during the session to adjust difficulty dynamically
- **Student “Homework Wrapped”** — a monthly student-facing recap showing progress (practice time, topics covered, error types mastered, confidence trend)
- **RL reward signal** — log `(mode, retry_count, feedback)` and train a bandit on teacher acceptance rate
- **Multi-session memory** — avatar remembers recurring mistakes across sessions to personalize coaching
