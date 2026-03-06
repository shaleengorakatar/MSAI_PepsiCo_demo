# Control Design Assessment API

FastAPI backend for the Control Design Assessment tool. Provides AI-powered process analysis, global/local control management, fit-gap analysis, and predictive risk monitoring.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env with your API keys

# 4. Run the server
uvicorn app.main:app --reload --port 8000
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Endpoints

### AI Analysis
- `POST /api/analyze-source` – Analyze interview/SOP text with LLM to extract process steps, risks, and inefficiencies

### Global / Local Controls
- `POST /api/baselines` – Create a Global Baseline Control
- `GET /api/baselines` – List all baselines
- `GET /api/baselines/{id}` – Get baseline by ID
- `PUT /api/baselines/{id}` – Update baseline
- `DELETE /api/baselines/{id}` – Delete baseline
- `POST /api/variations` – Create a Local Market Variation (inherits from a baseline)
- `GET /api/variations` – List variations (optionally filter by `baseline_id`)
- `GET /api/variations/{id}` – Get variation by ID
- `PUT /api/variations/{id}` – Update variation
- `DELETE /api/variations/{id}` – Delete variation

### Fit-Gap Engine
- `POST /api/fit-gap` – Compare a market variation against its global baseline

### Predictive Risk Monitoring
- `POST /api/monitoring/ingest` – Ingest performance data points
- `POST /api/monitoring/generate-mock/{baseline_id}` – Generate mock performance data
- `GET /api/monitoring/report/{baseline_id}` – Get predictive risk report

### Health
- `GET /health` – Health check

## Architecture

- **Data Models**: Pydantic schemas with `MultiLangText` for multi-language metadata
- **Global/Local Pattern**: `GlobalBaselineControl` defines the standard; `LocalMarketVariation` inherits and overrides specific steps
- **Fit-Gap Engine**: Compares local vs global, scores alignment (0-100%), flags gaps
- **LLM Integration**: Configurable OpenAI or Anthropic provider via `LLM_PROVIDER` env var
- **CORS**: Pre-configured for `*.lovable.app` and local dev origins

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `openai` or `anthropic` | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | – |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o` |
| `ANTHROPIC_API_KEY` | Anthropic API key | – |
| `ANTHROPIC_MODEL` | Anthropic model name | `claude-sonnet-4-20250514` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,http://localhost:5173` |
