# Architecture Review

## Pros

### Clean pedagogical architecture
The system maps exercise modes (speaking, vocab, writing, grammar) to distinct avatar system prompts and student task lists. That's a real product insight — different pedagogy requires different AI behavior, and it's modelled explicitly rather than bolted on.

### Good resilience chain
Exercise generation cascades: real AI workflow → fallback prompts. Homework analysis cascades: Bedrock → Mistral → static fallback. The system degrades gracefully rather than crashing, which matters in a demo context.

### Stateless avatar sessions
The Anam session token flow is correctly stateless — the server just generates a token and hands it to the browser. The actual avatar session runs client-side via Anam's infrastructure. This means the server isn't holding open WebSocket connections or streaming audio; all of that scales with Anam.

### `chat_id` isolation is naturally scalable
Each assignment generates a UUID-based `chat_id` per mode. The ID scheme itself (`{uuid}-{mode}`) means thousands of concurrent sessions wouldn't conflict — the identifier design is already production-ready.

### Separation of concerns between teacher and student flows
Teacher creates → student practices → teacher reviews is a clean three-stage pipeline with distinct API endpoints for each stage.

---

## Cons and How You'd Scale Them

### 1. SQLite — the biggest bottleneck

**Problem:** Single file, one writer at a time (file-level locking). Falls over immediately under concurrent load.

**Scale path:** Drop-in replace with PostgreSQL (same schema, minimal code change since it's accessed through raw SQL, not an ORM). Add connection pooling via pgBouncer or SQLAlchemy's pool. For a SaaS product you'd then add row-level security policies tied to `tutorId`/`studentId` — those columns already exist in the schema, they just aren't used yet.

---

### 2. Synchronous AI calls block the HTTP thread

**Problem:** `generate_exercise` and `complete_homework` both call Bedrock/Mistral synchronously. A Bedrock call can take 5–30 seconds. Under load this exhausts FastAPI's worker threads.

**Scale path:** Move to an async task queue — Celery + Redis, or AWS SQS + Lambda. The endpoint returns a job ID immediately, the client polls or receives a webhook when done. This also makes retries and dead-letter queues trivial to add.

---

### 3. No authentication or multi-tenancy

**Problem:** Any request knowing a `chat_id` can read or overwrite any session's data. There's no concept of "this assignment belongs to teacher X's student Y."

**Scale path:** Add a lightweight auth layer (JWT via something like Auth0 or Supabase). Enforce `tutorId` as a foreign key from the JWT claims. Add a middleware check that verifies the requesting user owns the `chat_id` before serving it. The schema already has the columns — it's purely a wiring problem.

---

### 4. No rate limiting or cost controls

**Problem:** Every `/generate` request unconditionally calls Bedrock. A bad actor (or just a bug in the frontend) could trigger unlimited expensive AI calls.

**Scale path:** Rate limiting at the API gateway layer (e.g. AWS API Gateway, `nginx limit_req`, or a simple Redis token bucket per `tutorId`). Add per-user spend tracking in the DB so you can cap or throttle.

---

### 5. Worksheet files are parsed then discarded

**Problem:** Uploaded PDFs/images are written to a temp file, parsed, then deleted immediately. If parsing fails or you want to re-parse with a better model later, the file is gone.

**Scale path:** Upload to S3/GCS first with the `chat_id` as the key, then parse. Store the S3 key in the DB. This also enables async parsing (upload returns immediately, parsing happens in a background job) and lets you re-process files without re-uploading.

---

### 6. Single shared default instructions row

**Problem:** The `chat.default_instructions` key in SQLite is one global default for the entire deployment. Changing it affects everyone.

**Scale path:** Move per-teacher configuration to a `tutor_config` table keyed by `tutorId`. Each teacher gets their own default prompt, branding, or language settings.

---

### 7. No observability

**Problem:** Logging exists but there's no structured metrics, no tracing, no alerting. You can't tell if Bedrock is slow, which modes are most used, or what the error rate is.

**Scale path:** Add structured logging (JSON logs to CloudWatch/Datadog), instrument the AI call latencies as metrics, and add distributed tracing (OpenTelemetry) across the FastAPI + Bedrock + Anam hops.

---

## Latency & Cost Reductions

### 1. Parallelise the 4 sequential AI calls — ~75% latency reduction

**Problem:** In `cleanup.py:311-320`, `run_cleanup` loops through all 4 modes and calls Bedrock one at a time:

```python
for mode in MODES:
    mode_result = _run_single_mode(...)  # waits ~5-10s each
```

These calls are completely independent. Total wall time is roughly 4× per-call latency.

**Fix:** Run them concurrently with `asyncio.gather`. The async client (`generate_text_async`) already exists in `bedrock_backend.py:95-113` — it's just not wired up in the generation path. This alone cuts generation time by ~75%.

---

### 2. Prompt caching on the system prompt — ~40% cost reduction on cleanup

**Problem:** `CLEANUP_SYSTEM_PROMPT` is ~3,000 tokens and is sent on every one of those 4 calls — ~12,000 input tokens just for the system prompt per generation request.

**Fix:** Anthropic supports prompt caching via a `cache_control` parameter. Mark the system prompt as `"type": "ephemeral"` and Bedrock caches it for 5 minutes. The first call pays full price; calls 2–4 hit the cache at ~10% of the cost. For a task done 4 times in quick succession, this almost eliminates repeat system prompt costs.

---

### 3. Right-size `max_tokens` budgets

**Problem:** The cleanup task has `max_tokens = 2500` in the TOML, but the spec asks for 200–280 word prompts and 3 short tasks. Actual output is ~500–700 tokens. You're paying Bedrock to reserve capacity you never use, and slowing down calls since the model can produce up to that limit before stopping.

**Fix:** Tighten cleanup to ~900 tokens, report to ~400 (the report output is 4 short lines).

---

### 4. Right-size models — ~80% cheaper on OCR and analysis

**Problem:** Everything currently routes to Claude Sonnet 4.6 on Bedrock. Some tasks don't need it.

| Task | Current | Better | Reason |
|---|---|---|---|
| OCR structuring | Sonnet | Haiku | Extracting structured JSON from a page, not reasoning |
| Homework analysis | Sonnet | Haiku | Short structured output, low creativity needed |
| Exercise generation | Sonnet | Keep | Quality matters here |

Haiku is ~20× cheaper and significantly faster than Sonnet. Switching OCR and analysis would meaningfully cut per-session cost.

---

### 5. Singleton Bedrock client

**Problem:** In `bedrock_backend.py:25-27`, `_client()` creates a new `AnthropicBedrock` instance on every call, re-establishing the connection each time.

**Fix:** Make the client a module-level singleton — instantiate once, reuse. Minor latency saving but essentially free to implement.

---

### 6. Cache worksheet OCR by file hash

**Problem:** There's already an `ocr/cache.py` file. If a teacher re-generates assignments (e.g. with different feedback), the worksheet gets re-parsed from scratch every time even though the file hasn't changed.

**Fix:** Cache the OCR result by file hash. Subsequent generations skip the Bedrock vision call entirely — saving ~5–10s and one full vision call per re-generation.

---

### Priority summary

| Change | Effort | Latency impact | Cost impact |
|---|---|---|---|
| Parallelise 4 mode calls | Low | ~75% reduction | None |
| Prompt caching on system prompt | Low | Minor | ~40% reduction on cleanup |
| Right-size `max_tokens` | Trivial | Minor | Small |
| Haiku for OCR + analysis | Low | Faster | ~80% cheaper on those tasks |
| Singleton Bedrock client | Trivial | Minor | None |
| Cache OCR by file hash | Medium | Saves ~5–10s on re-generate | Saves 1 vision call |

---

## Summary

The system is architected correctly — the right abstractions exist and the data model is reasonable — but every persistence and compute operation is implemented for one user on one machine. The path to scale is mostly about replacing the transport layer (SQLite → Postgres, sync calls → queues) without rethinking the domain model.

When LlamaIndex becomes worth it

I’d switch to LlamaIndex + OpenAI when one or more of these become true:

teachers upload multiple worksheets per course

you want to store parsed worksheets and reuse them later

you want chunking/retrieval instead of manual excerpt heuristics

you want query-engine style access over lesson materials

you want to rank relevant worksheet chunks by the requested topic

---

👉 add LLM-based style analysis node (instead of heuristic)
👉 or add retrieval over multiple worksheets (mini-RAG)
