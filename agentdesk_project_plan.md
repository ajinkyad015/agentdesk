# AgentDesk API
### Production-Grade Tool-Calling LLM Agent Backend

**One-liner:** A FastAPI backend where a user chats with an AI agent that can actually *do things* — check the weather, do math, manage a to-do list — by deciding which tools to call, executing them, and streaming the answer back over SSE.

**Difficulty:** Moderate. No RAG, no multi-agent orchestration, no Kubernetes. One agent, a handful of real tools, real persistence, real production hygiene.

| | |
|---|---|
| **Type** | LLM agent backend (tool-calling / function-calling) |
| **Core skills** | Async FastAPI, Postgres persistence, LLM tool-calling, SSE streaming, rate limiting, structured logging, mocked-LLM testing |
| **Time, full-time pace** | ~10–15 focused days (see [Pacing](#20-pacing-across-your-15–20-days) at the end) |
| **Cost to build** | Low single-digit dollars if you use a cheap/fast model and mock the LLM in tests (below) |

---

## 0. Read this part first — the honest tradeoff of switching projects

This will take longer than the "bolt a feature onto IssueForge" plan we discussed. That's the real cost of starting fresh. Two things make it worth it and keep it fast:

1. **Reuse your plumbing, don't rewrite it.** Copy your config loader, logging middleware, DB session dependency, and API-key auth pattern from IssueForge straight into this new repo as a starting scaffold. New domain, new resume line, new agent logic — but not new boilerplate. That's the single biggest time-saver available to you here.
2. **Milestones 1–7 are your "must-ship" core** (~10-11 days). Milestones 8-10 and the stretch goals are real but can run in parallel with deploying and applying, not before it. Don't let this document's thoroughness talk you into perfectionism — that directly works against your 15–20 day goal. More on this at the end.

---

## 1. Why this project

IssueForge proved you can build a layered FastAPI app with DI, SQLAlchemy, Alembic, and exception handling. That's not discarded — it's the foundation this stands on. What's new here is the part that actually gets you filtered *in* for "AI engineer" roles instead of "backend intern": an LLM deciding which tools to call, a loop that executes them safely, and a stream back to the client. That loop, done properly, is the literal day-to-day work of the role you're applying for.

## 2. Scope discipline — what this deliberately excludes

- No RAG / embeddings / vector DB — that's a separate, later project (don't mix it in here, it roughly doubles the scope).
- No multi-agent handoff / supervisor patterns.
- No Kubernetes or service mesh.
- No full tracing stack (OpenTelemetry, Jaeger) — structured logs are enough at this scale.
- No full OAuth/JWT — a simple hashed API key is enough to prove auth *and* user isolation, which is the part that actually matters here.

"Moderate" means real, but bounded. Every one of the above is a legitimate stretch goal for later, not a requirement now.

## 3. Concepts

**New concepts this project introduces**
- LLM tool-calling / function-calling (structured, via the provider's native `tools` API — not a hand-parsed "Action: ..." text hack)
- Agent loop design: bounded iterations, tool execution, errors fed back as observations instead of crashing
- Async LLM API client, both non-streaming and streaming
- SSE event *framing* — named events (`token`, `tool_call`, `tool_result`, `done`, `error`), not just raw text chunks
- Token usage / cost tracking
- Rate limiting, hand-rolled before reaching for a library
- Prompt injection via tool output, as a concrete security concern
- Protocol-based provider abstraction (swap LLM vendors without touching the loop)

**Concepts reinforced from IssueForge**
- FastAPI routing, Pydantic v2 schemas
- Dependency injection, layered (router → service → repository) architecture
- SQLAlchemy models + Alembic migrations
- API-key authentication
- Structured logging middleware
- Custom exception handling / error contracts
- Async/await, timeouts, retries
- Docker + docker-compose

## 4. Functional requirements

- A user can register and receive an API key.
- A user can create a conversation and send it messages.
- The agent decides, per message, whether to answer directly or call one or more tools before answering.
- Available tools: **calculator**, **get_weather**, and **tasks** (create / list / complete a to-do item).
- The agent can chain tool calls (e.g., check weather, then create a task) up to a bounded number of iterations.
- Responses stream to the client over SSE as they're generated.
- Conversation and message history persist and are retrievable across sessions.
- A user cannot see or modify another user's conversations or tasks.
- Requests are rate-limited per user.
- A parallel plain REST CRUD surface exists for tasks (not just via the agent), sharing the same service layer.

## 5. Non-functional requirements

- **Performance:** measure and report p50/p95 time-to-first-SSE-byte; the app's own overhead (auth, DB, rate-limit check) should be a small fraction of total latency compared to the LLM call itself.
- **Reliability:** every external call (LLM, weather API) has an explicit timeout and a bounded retry with backoff; the agent loop has a hard iteration cap with a graceful fallback, never an infinite loop or an unbounded bill.
- **Security:** every query is scoped to the authenticated user; tool arguments coming from the LLM are validated before execution, never `eval()`'d; API keys are stored hashed, never in plaintext.
- **Maintainability:** adding a new tool should mean writing one function and one schema entry — not touching the agent loop's control flow.

## 6. Tech stack

| Category | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Database | PostgreSQL |
| Migrations | Alembic |
| Validation | Pydantic v2 + pydantic-settings |
| LLM SDK | `anthropic` (AsyncAnthropic) and/or `openai` (AsyncOpenAI) — behind your own Protocol |
| HTTP client (tools) | httpx (async) |
| Weather source | Open-Meteo — free, no API key required, good for a learning project |
| Streaming | Starlette `StreamingResponse` with hand-written SSE framing |
| Rate limiting | hand-rolled in-memory token bucket first; `slowapi` as an optional later swap |
| Logging | Python `logging` with a JSON formatter + a request-id contextvar |
| Testing | pytest, pytest-asyncio, httpx `AsyncClient` |
| Containerization | Docker + docker-compose |

**On LLM choice:** either Anthropic or OpenAI works fine — that's exactly why the Protocol abstraction below matters. Use a cheap, fast model for development (e.g., Claude Haiku or GPT-4o-mini). Because the LLM client is mocked in your test suite (Milestone 5), your test run costs $0; only your own manual smoke-testing during development touches the real API, and at a cheap model's rates a full build-and-test cycle should stay well under a few dollars.

## 7. Architecture

```
Client (curl / simple HTML+SSE demo page)
        │
        ▼
   FastAPI App
        │
        ├── Middleware: request-id, structured JSON logs, timing
        │
        ▼
  Auth Dependency (API key → current_user)
        │
        ▼
  Rate Limiter Dependency (per-user token bucket)
        │
        ▼
   Router: POST /conversations/{id}/messages   (SSE response)
        │
        ▼
   Agent Service ───────────────┐
        │                       │
        ▼                       ▼
  LLM Client (async,       Tool Registry
  Anthropic or OpenAI,      ├── calculator        (pure function)
  behind a Protocol)        ├── get_weather        (httpx + timeout/retry → Open-Meteo)
        │                   └── tasks tool         (→ Task Repository → Postgres)
        │                       │
        └───────────◄───────────┘
        (loop: tool result fed back into the LLM until a final answer or the iteration cap)
        │
        ▼
  Message Repository ──► PostgreSQL (users, conversations, messages, tasks)
        │
        ▼
  SSE stream back to client:  token / tool_call / tool_result / done / error events
```

## 8. Folder structure

```
agentdesk/
├── app/
│   ├── api/v1/routers/       # auth.py, conversations.py, messages.py, tasks.py, health.py
│   ├── core/
│   │   ├── config.py          # pydantic-settings
│   │   └── logging.py         # JSON structured logging + request-id contextvar
│   ├── db/
│   │   ├── database.py
│   │   ├── session.py
│   │   └── base.py
│   ├── dependencies/           # current_user, rate_limiter, db_session
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                 # Pydantic request/response models
│   ├── repositories/            # DB access, one per aggregate (users, conversations, messages, tasks)
│   ├── services/
│   │   ├── agent_service.py     # the agent loop lives here
│   │   ├── conversation_service.py
│   │   └── tool_registry.py     # maps tool name → schema + callable
│   ├── tools/                   # calculator.py, weather.py, tasks_tool.py — pure, independently testable
│   ├── llm/
│   │   ├── client.py            # LLMClient Protocol
│   │   ├── anthropic_client.py
│   │   ├── openai_client.py
│   │   └── fake_client.py       # scripted responses, used in tests
│   ├── middleware/
│   ├── exceptions/
│   └── main.py
├── alembic/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
├── demo/                         # optional minimal HTML + EventSource demo page
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

**Responsibility notes:** `tools/` contains plain async functions with no knowledge of the LLM — they should be fully unit-testable in isolation (Milestone 4, before any agent code exists). `llm/` is the only layer that talks to a model provider; everything else depends on the `LLMClient` Protocol, not a concrete SDK. `services/agent_service.py` owns the loop and is the only place that should ever import both `llm/` and `tools/`.

## 9. Database schema

- **users** — `id` (UUID PK), `api_key_hash` (unique, indexed), `display_name`, `created_at`
- **conversations** — `id` (UUID PK), `user_id` (FK → users, indexed), `title`, `created_at`, `updated_at`
- **messages** — `id` (UUID PK), `conversation_id` (FK → conversations, indexed), `role` (enum: `user` / `assistant` / `tool`), `content` (text), `tool_name` (nullable), `tool_call_id` (nullable), `tool_input` (jsonb, nullable), `tool_output` (jsonb, nullable), `sequence_number` (int), `created_at`
- **tasks** — `id` (UUID PK), `user_id` (FK → users, indexed), `title`, `is_done` (bool, default false), `due_date` (nullable), `created_at`, `updated_at`

**Indexes worth adding on purpose (not by accident):** `messages(conversation_id, sequence_number)` for ordered history reads; `tasks(user_id, is_done)` for the common "show my open tasks" query; `conversations(user_id, updated_at desc)` for listing recent conversations.

## 10. API endpoints

| Method | Path | Body | Response | Auth | Errors |
|---|---|---|---|---|---|
| POST | `/api/v1/auth/register` | `{display_name}` | `{api_key, user_id}` (key shown once) | none | 400 |
| POST | `/api/v1/conversations` | `{title?}` | `{id, title, created_at}` | required | 401 |
| GET | `/api/v1/conversations` | – | `[{id, title, updated_at}]` | required | 401 |
| GET | `/api/v1/conversations/{id}/messages` | – | `[{role, content, ...}]` | required | 401, 403, 404 |
| POST | `/api/v1/conversations/{id}/messages` | `{content}` | **SSE stream** — see §11 | required | 401, 403, 404, 429, 502, 504 |
| GET | `/api/v1/tasks` | – | `[{id, title, is_done, ...}]` | required | 401 |
| POST | `/api/v1/tasks` | `{title, due_date?}` | `{id, title, ...}` | required | 401, 400 |
| PATCH | `/api/v1/tasks/{id}` | `{is_done?, title?}` | `{id, ...}` | required | 401, 403, 404 |
| GET | `/health` | – | `{status: "ok"}` | none | – |

## 11. Agent loop design — the heart of the project

**Sequence per user message:**
1. Load conversation history from the DB.
2. Persist the new user message.
3. Call the LLM with: system prompt + message history + tool schemas.
4. LLM responds with either plain text (done) or one or more tool-use requests.
5. If tool(s) requested: validate the arguments against the tool's schema, execute with a timeout, capture the result *or* the error, append both the tool call and its result as messages, then go back to step 3.
6. Cap the loop at a fixed number of iterations (e.g., 5). If the cap is hit, return a graceful fallback message — never an exception, never an infinite bill.
7. Once the LLM returns a final plain-text answer: persist it, stream it to the client, and emit a `done` event with usage metadata.

**Shape of the loop (not a solution — write the real version yourself):**
```
loop up to MAX_ITERATIONS:
    response = await llm_client.generate(messages, tools)
    if response.stop_reason == "tool_use":
        for call in response.tool_calls:
            result_or_error = await execute_tool(call)   # validated args, timeout, caught exceptions
            messages.append(tool_result_message(call, result_or_error))
        continue
    else:
        return response.text
else:
    return FALLBACK_MESSAGE
```

**SSE event schema** (named events, not raw text — this is the part most beginners skip):
```
event: token
data: {"delta": "Hello"}

event: tool_call
data: {"name": "get_weather", "input": {"location": "Pune"}}

event: tool_result
data: {"name": "get_weather", "output": {"temp_c": 31}}

event: done
data: {"usage": {"input_tokens": 120, "output_tokens": 45}, "tools_used": ["get_weather"]}

event: error
data: {"message": "upstream LLM timeout"}
```

**Questions to be able to answer out loud before you move on** (these are also in your interview-question list at the end, but answer them for yourself first):
- Why cap the loop at all?
- Why validate tool arguments even though they came from *your own* LLM call, not directly from the user?
- Why does execution/DB-writing live in the service layer instead of the router?
- Why should a tool's *output* be treated as untrusted content once it goes back into the prompt?

## 12. Milestones

| # | Milestone | Est. time | Key thing to nail | How you know it works |
|---|---|---|---|---|
| 1 | Skeleton: FastAPI app, pydantic-settings config, docker-compose (app + Postgres), `/health`, JSON logging middleware with request-id | ~1 day | Reuse IssueForge's config/logging, don't rewrite | `docker-compose up`; `curl /health` returns 200 and the log line carries a request-id |
| 2 | Data layer: models, one Alembic migration, repositories, repo-level tests | ~1.5 days | Relationships, indexes, migrations | `alembic upgrade head` runs clean; repo tests pass against a real test DB |
| 3 | Auth: hashed API key, `/auth/register`, `current_user` dependency, ownership checks on every query | ~1 day | *User-scoped* queries, not just "logged in" | Write a test proving user B cannot read user A's tasks or conversations |
| 4 | Tools as standalone services: calculator (no `eval`), weather (httpx + timeout + retry), tasks CRUD — **zero LLM code yet** | ~1.5 days | Tools are just functions; prove them without any agent | Each tool has unit tests that never touch an LLM |
| 5 | LLM client + one non-streaming round trip: `LLMClient` Protocol, one real client, a `FakeLLMClient`, one tool call end-to-end (no loop, no streaming yet) | ~2 days | Provider abstraction + mocked-LLM testing | A test using `FakeLLMClient` proves "2+2 → calls calculator → returns 4" with zero real API calls |
| 6 | Full loop: multiple sequential tool calls, iteration cap, tool errors fed back as observations, not exceptions | ~2 days | Bounded loops; errors-as-data | Force a tool to fail with bad args; confirm the agent recovers or gives up gracefully — never a 500 |
| 7 | SSE streaming: named events, handle client disconnect (stop generating, don't burn tokens for nobody) | ~2 days | Real SSE framing + cancellation | Open the stream, kill the client mid-response, confirm the server stopped generating |
| 8 | Rate limiting + observability: hand-rolled per-user token bucket, structured logs with conversation id / tool names / latency / token usage | ~1 day | Understand a token bucket before you'd import one | Fire 20 rapid requests; confirm 429s past the limit and genuinely useful log lines |
| 9 | Failure injection: work the debugging list in §14, one regression test per bug | ~1.5 days | Turning bugs into permanent tests | Every bug has a red test before the fix, green after |
| 10 | Docker/CI/README/demo: multi-stage Dockerfile, CI running lint + tests, README with the architecture diagram, and (strongly recommended) a tiny HTML + `EventSource` page for a demo recording | ~1.5 days | Shippability | A stranger can `docker-compose up`, open the demo page, and watch the agent stream a tool-using answer |

**Milestones 1–7 (~10–11 days) are the must-ship core.** 8–10 are real, but can happen in parallel with deploying and applying — see §20.

## 13. Testing strategy

- **Unit:** each tool in isolation; the agent loop against `FakeLLMClient` scripted to emit specific tool-call sequences; the rate limiter in isolation.
- **Integration:** real Postgres (test DB or per-test transactional rollback); full request→response through FastAPI's `AsyncClient` with `FakeLLMClient` injected via a **dependency override** — this is exactly what `Depends` overrides are for.
- **API/contract:** status codes, error response shapes, and SSE event framing (parse the actual event stream in the test, don't just check for 200).
- **Concurrency:** two simultaneous messages in one conversation — assert `sequence_number` never collides; concurrent requests against the rate limiter from the same user.
- **Failure injection:** simulated LLM timeout, simulated tool exception, simulated malformed tool arguments from the LLM — all easy to script via `FakeLLMClient`.

## 14. Debugging / failure challenges

No solutions here — these are for you to hit, or deliberately introduce and then fix, milestone by milestone. Say "start milestone 9" (or any milestone) when you get there and I'll mentor you through them PR-review style, hints first.

- Infinite tool-call loop — the LLM keeps calling a tool without ever converging.
- A tool timeout that isn't surfaced properly — the request just hangs.
- Race condition: two messages land concurrently in the same conversation.
- Cross-user data leak — a query missing a `user_id` filter.
- Prompt injection via tool output — a tool result containing text designed to redirect the agent.
- Blocking call inside an async endpoint — e.g., a synchronous HTTP call inside an `async def` tool, stalling the event loop.
- SSE connection drop mid-stream — the client disconnects; does the server keep burning tokens anyway?
- Retry storm — naive retry-without-backoff on a 429 from the LLM provider, making the problem worse.

## 15. Performance challenges

- Reduce time-to-first-SSE-byte; measure p50/p95 before and after.
- Handle 50–100 concurrent chat requests without exhausting the DB connection pool.
- If you support parallel tool calls in one turn, bound concurrent tool execution so one message can't spawn unbounded outbound calls.
- Measure the tasks CRUD endpoints' latency separately from the agent endpoint, so you can tell "your code" latency apart from "waiting on the LLM" latency.

## 16. Definition of done

- [ ] Agent correctly picks from 3+ distinct tools based on natural language — no hardcoded keyword routing.
- [ ] At least one turn involves 2+ sequential tool calls, and the loop is capped with a graceful fallback.
- [ ] Conversation/message history persists and multi-turn context actually works.
- [ ] User-scoped auth is enforced everywhere; cross-user access returns 403/404, never data.
- [ ] SSE streaming works, and a client disconnect measurably stops server-side work.
- [ ] Rate limiting returns 429 with a clear body when exceeded.
- [ ] Every external call (LLM, weather) has an explicit timeout and a bounded retry.
- [ ] Malformed tool arguments from the LLM are rejected without crashing the process.
- [ ] Structured logs include request id, conversation id, tool names, latency.
- [ ] The LLM client is mocked in tests — the suite runs with zero real API calls and zero cost.
- [ ] Unit, integration, and at least one concurrency test pass in CI.
- [ ] `docker-compose up` brings up app + DB cleanly from a fresh clone.
- [ ] README documents the architecture and includes a demo GIF.
- [ ] You can explain, out loud, *why* every one of the above is true — that's the actual bar.

## 17. Interview questions

1. Walk me through what happens, end to end, when a message triggers two sequential tool calls before a final answer.
2. Why did you cap the agent's loop, and what happens when the cap is hit?
3. How do you prevent one user from reading another user's conversations or tasks?
4. Your weather call hangs for 30 seconds — what's happening to the request, and how did you prevent it?
5. Why validate tool arguments when they came from your own LLM call, not directly from the user?
6. How would you add a new tool without touching the core loop?
7. Two requests arrive concurrently for the same conversation — what guards against a collision?
8. Why is the LLM client mocked in tests instead of hitting the real API?
9. A client disconnects mid-stream — what happens server-side, and why does that matter for cost?
10. What's the actual risk if a tool's output contained the text "ignore previous instructions," and how would you mitigate it?

## 18. Open-source study guide

Trace **one request** through each of these — don't read either repo cover to cover.

**1. `anthropics/claude-cookbooks` — `tool_use/` directory.** Look at `calculator_tool.ipynb` first (simplest possible tool loop), then `customer_service_agent.ipynb` (a fuller agent with multiple tools) and `parallel_tools.ipynb` (concurrent tool calls, relevant if you attempt that stretch goal). Trace: how is a tool schema defined, how is the response checked for a tool-use stop reason, how is the tool result formatted going back into the message list. Skip anything involving RAG/vector DBs in that repo for now — not this project. Recreate the calculator flow yourself in Milestone 5 without copying the notebook's code.

**2. `openai/openai-cookbook` — `examples/How_to_call_functions_with_chat_models.ipynb`.** This is the canonical walkthrough of the "check finish_reason, extract function name + args, call it, append the result, call again" cycle — the same shape as your loop in §11. Skip `Function_calling_with_an_OpenAPI_spec.ipynb` and the fine-tuning notebook for now; both are beyond this project's scope. Recreate the core loop yourself; don't adapt their code directly.

**3. Your own IssueForge repo.** Genuinely the most useful reference for the plumbing: reread your own config loader, logging middleware, DB session dependency, and auth pattern before rebuilding similar pieces here. You already know why you made those choices — reuse that reasoning.

## 19. Stretch goals (optional — do these in parallel with applying, not before)

- Idempotency key on the send-message endpoint, so a flaky client retry can't trigger a second LLM call and double the cost.
- Auto-generate a conversation title from the first message via a cheap LLM call.
- Bounded-concurrency parallel tool execution when the LLM requests more than one tool call in a turn.
- Swap in a second LLM provider to prove the Protocol abstraction actually holds up.
- A simple `/metrics` counter (requests, tool calls by name, tokens used) — a lightweight taste of observability without a full tracing stack.

## 20. Pacing across your 15–20 days

Milestones 1–7 are roughly 10–11 focused days at full-time pace — that's a genuinely demo-able agent: persistence, auth, real tools, a real loop, real streaming. Treat that as your ship point. Deploy it, record the demo, rewrite your resume bullets around it, and start applying with *that* version. Milestones 8–10 (rate limiting polish, failure-injection hardening, Docker/CI/demo-page polish) and the stretch goals are worth doing, but they should run alongside outreach, not gate it — the same principle from our first conversation: use the days to be maximally ready and applying, not waiting for 100% before you start.

## Next step

Say **"start milestone 1"** and I'll run it the way you set up in your original roadmap: I'll ask you to propose the approach before either of us writes a line of code.
