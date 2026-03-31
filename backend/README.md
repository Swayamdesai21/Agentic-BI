# Agentic BI — Backend

Natural language to live business dashboard, powered by LangGraph + Groq.

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env and add your free Groq API key from https://console.groq.com

# 4. Run the server
uvicorn main:app --reload --port 8000
```

The database will auto-seed with sample e-commerce data on first run.
