# GP Farm Q&A

Runnable multi-agent-style Q&A assistant based on `context.md`.

## Run

```bash
python -m qagpfarm.qa --offline "giá granola không yến mạch"
```

Run through LangGraph:

```bash
python -m qagpfarm.qa --offline --langgraph "tư vấn quà tặng cao cấp"
```

Run the simple web UI:

```bash
python -m qagpfarm.web --offline
```

Then open `http://127.0.0.1:8000`.

Run the web UI with streamed answers from the same QA streaming path:

```bash
OPENAI_BASE_URL=http://localhost:20128/v1 \
OPENAI_API_KEY=local-proxy-key \
OPENAI_MODEL=cx/gpt-5.3-codex-none \
python -m qagpfarm.web --stream
```

With an OpenAI-compatible local proxy:

```bash
OPENAI_BASE_URL=http://localhost:20128/v1 \
OPENAI_API_KEY=local-proxy-key \
OPENAI_MODEL=cx/gpt-5.3-codex-none \
python -m qagpfarm.qa "tư vấn quà tặng cao cấp"
```

Continuous chat with model answers:

```bash
OPENAI_BASE_URL=http://localhost:20128/v1 \
OPENAI_API_KEY=local-proxy-key \
OPENAI_MODEL=cx/gpt-5.3-codex-none \
python3 -m qagpfarm.qa --langgraph --chat
```

Stream one model answer:

```bash
OPENAI_BASE_URL=http://localhost:20128/v1 \
OPENAI_API_KEY=local-proxy-key \
OPENAI_MODEL=cx/gpt-5.3-codex-none \
python3 -m qagpfarm.qa --stream "tư vấn granola ăn kiêng"
```

`context.md` remains the source of truth for prompts, products, prices, and contact information.
