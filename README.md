# TailMemory

> A maintenance assistant that remembers what every previous shift already tried on this airframe.

TailMemory is an advisory prototype for aircraft maintenance teams. A user selects a synthetic aircraft tail number, describes a current fault, recalls relevant history from Hindsight Cloud, and receives a structured Groq advisory grounded in that aircraft-specific evidence.

## Why persistent memory matters

Without memory, an assistant can recommend a generic intervention that the aircraft has already tried. TailMemory makes the remembered history visible and marks previously failed actions so a qualified engineer can review a different verification path.

## Architecture

```text
Streamlit UI
  ├── HindsightClient -> Hindsight Cloud retain/recall
  ├── DiagnosisAgent -> Groq structured JSON
  ├── Pydantic validation
  └── synthetic CSV + FAA SDR terminology sample
```

Hindsight is the persistent memory engine. The client uses the verified Hindsight Cloud REST API:

- `POST /v1/default/banks/{bank_id}/memories` for synchronous retain
- `POST /v1/default/banks/{bank_id}/memories/recall` for semantic recall
- `Authorization: Bearer hsk_...`
- `tail:{tail_number}` tags with exact matching for aircraft isolation

No local dictionary, browser memory, JSON file, SQL table, or vector database substitutes for Hindsight.

## Data and disclosure

The demonstration dataset contains eight synthetic tail numbers with 20-24 events each. Five tails contain planted failed-fix chains. `data/faa_sdr_sample.csv` is a small, clearly labeled sample used only for vocabulary and domain context. FAA narratives are never presented as records for the synthetic aircraft.

> This prototype uses synthetic per-tail maintenance histories and FAA Service Difficulty Report narratives for terminology/context. It is not an aircraft maintenance authorization, airworthiness, or certification system.

## Setup

Python 3.11+ is recommended.

```bash
cd tailmemory
python -m pip install -r requirements.txt
cp .env.example .env
python -m app.data.generator
python -m evaluation.evaluate
python docs/architecture.py
```

Set these values in Replit Secrets or `.env` locally:

```env
GROQ_API_KEY=
HINDSIGHT_API_KEY=
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_BANK_ID=
```

The app refuses to run a live diagnosis when keys are missing. It does not silently switch to fake memory or fake model responses.

## Run

```bash
streamlit run app/main.py --server.port 5000
```

## Demo flow

1. Select `VT-ABC`.
2. Keep the prefilled hydraulic pressure warning.
3. Run a configured diagnosis.
4. Inspect the Hindsight Memory Inspector and the two failed pump-replacement memories.
5. Review the advisory and record `DID NOT WORK`, which is retained as a new Hindsight memory.
6. Repeat the same fault to see the feedback loop.
7. Select `VT-XYZ` to demonstrate that the same fault has no VT-ABC aircraft-specific evidence.

## Evaluation

`python -m evaluation.evaluate` produces `evaluation/results/results.csv` and `evaluation/results/results.png`. The current offline evaluation is explicitly labeled a deterministic evidence proxy: it measures actual held-out synthetic cases without inventing percentages or using an LLM as judge. Live LLM-arm benchmarking requires configured Groq and Hindsight credentials and should be run separately before making comparative claims.

## Testing

```bash
pytest -q
```

Tests cover Pydantic validation, synthetic data generation, failed-fix chains, tail isolation, empty memory handling, and explicit missing-configuration errors.

Once the required secrets and bank ID are configured, the real integration smoke test is:

```bash
python scripts/hindsight_smoke_test.py
```

## Safety boundary

TailMemory must not claim to diagnose an aircraft with certainty, certify airworthiness, authorize maintenance, replace qualified personnel, or provide dangerous procedural instructions. Every advisory includes a safety notice and is intended only for review by appropriately qualified personnel.
