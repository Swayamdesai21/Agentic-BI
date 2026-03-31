<div align="center">
  
# 🤖 Agentic BI: Natural Language to Live Business Dashboard

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain)](https://langchain.com/)
[![Groq](https://img.shields.io/badge/Groq-f55036?style=for-the-badge&logo=groq)](https://groq.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

Ask questions in plain English. AI agents build and update your dashboards autonomously.

</div>

---

## 💼 The ₹500 Crore Business Problem

Every large enterprise faces the same massive data bottleneck: **Business leaders can't get answers fast enough.** 

When a VP needs a new metric ("What's our revenue by region segmented by product category for Q3?"), they submit a Jira ticket. A data analyst writes the SQL, a BI engineer builds the Tableau/PowerBI dashboard, and 2 weeks later, the insight is delivered. By then, the business opportunity might be gone.

**This is a ₹500 Crore problem:**
- Analytics teams are extremely expensive and constantly backlogged.
- Decision-making velocity is crippled.
- Tool subscriptions (Looker, PowerBI) cost millions but adoption remains low because business users don't know how to build charts.

### The Solution: Agentic BI
Agentic BI entirely removes the technical bottleneck. It allows any non-technical business user to type a question in plain English and instantly receive an interactive, production-ready dashboard. **Every business user becomes an instant data analyst.**


---

## 🚀 How It Works (The Multi-Agent Architecture)

This isn't a simple ChatGPT wrapper. It is a highly robust **LangGraph multi-agent system** with a built-in self-correction loop to ensure absolute data accuracy.

When a user asks a question, 4 specialized AI agents work in sequence:

1. **🕵️ Query Agent**: Uses RAG (ChromaDB) over the database schema to convert the user's plain English into accurate, optimized SQL.
2. **🛡️ Validator Agent**: Test-executes the SQL against the database. If it hits an error (e.g., syntax error, missing column), it feeds the error back to the Query Agent in an automated **self-correction loop** (up to 3 retries) before ever failing.
3. **📊 Visualization Agent**: Analyzes the shape of the returning data (Time series? Categorical? Proportions?) and autonomously selects the mathematically optimal chart type (Line, Bar, Pie, Area) and returns a Pydantic-validated JSON configuration.
4. **📝 Narrative Agent**: Analyzes the raw data to extract actionable business insights and outputs a concise, plain-English executive summary.

All of this happens in milliseconds, streamed directly to a Next.js frontend via Server-Sent Events (SSE).

---

## 🛠️ Tech Stack & Implementation Details

The entire architecture is built using 100% free, cutting-edge, open-source tools.

### Backend (The Brain)
- **Framework**: FastAPI (Handles the SSE stream for the UI pipeline)
- **LLM**: Groq API (`llama-3.3-70b-versatile`) — Chosen for ultra-low latency inference.
- **Orchestrator**: LangGraph (State graph, cyclic self-correction loops)
- **RAG**: ChromaDB (Stores table structures, relationships, and sample queries for context retrieval)
- **Data Source**: SQLite (Ships with a seeded synthetic e-commerce dataset for zero-setup demoing)
- **Validation**: Pydantic

### Frontend (The Dashboard)
- **Framework**: Next.js 14 App Router
- **Styling**: Tailwind CSS (Premium dark mode, glassmorphism UI, dynamic CSS grid)
- **Charts**: Recharts (Dynamically reads the Pydantic JSON config to generate React charts)
- **State Flow**: Custom SSE client to render real-time LangGraph agent "thinking" statuses.

---

## 💻 Running the Project Locally

### 1. Start the Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create your .env and add your Groq key
cp .env.example .env
# Edit .env -> GROQ_API_KEY=your_key_here

# Run the API
uvicorn main:app --reload --port 8000
```
*(On first run, the SQLite database will auto-seed with over 500 rows of realistic e-commerce data!)*

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser. Try asking:
- *"Show me monthly revenue trends"*
- *"What are our top 5 best selling products by revenue?"*
- *"Show me customer segment breakdown"*

---

## 📈 Industry Context
The $26B BI market is actively being disrupted. Gartner predicts "BI Agents" will replace standard dashboards entirely. Companies like Wolters Kluwer are already prototyping financial conversational dashboards. 

This project demonstrates production-grade agentic design patterns that data teams at Enterprise tech companies are actively trying to build right now.
