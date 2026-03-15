# Portfolio Monitor

Automated monitoring for Mehdi's 5 AI portfolio projects.

## Projects monitored

| Project | Backend URL | Status |
|---------|------------|--------|
| DocuQuery AI | https://docuquery-ai-5rfb.onrender.com | monitored |
| WatchNext | https://watchnext-flta.onrender.com | monitored |
| DataPilot | https://datapilot-ogct.onrender.com | monitored |
| FeedbackSort | https://feedbacksortopenai-api-key.onrender.com | monitored |
| EvalKit | https://evalkit-vw7k.onrender.com | monitored |

## 3 modes

### 1. Health Check (free, fast)
```bash
python monitor.py health
```
Pings `/health` on all backends. No OpenAI cost.

### 2. Smoke Test (few cents)
```bash
python monitor.py smoke
```
Sends one real request per service, validates the response structure.

### 3. Pre-Demo Warmup
```bash
python monitor.py predemo
```
Wakes up all Render backends (cold start), then runs smoke tests.
Ideal: run 5 min before a demo.

## Automated (GitHub Actions)

- Health check: every 6 hours
- Smoke test: daily at 8am UTC
- Email alert on failure

## Local setup

```bash
pip install -r requirements.txt
cp .env.example .env  # add your OPENAI_API_KEY
python monitor.py health
```
