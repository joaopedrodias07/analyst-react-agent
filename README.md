# 🤖 Analyst Agent — Sales Analysis Agent

AI-powered conversational agent that analyzes sales data through natural language. Built with LangGraph and DeepSeek.

## Features

- Natural language to SQL queries
- Financial analysis with insights and recommendations
- Chart generation (line, bar, pie, histogram)
- PDF report generation
- Email delivery with attachment
- Conversational memory per session

## Architecture

The agent uses a deterministic intent classifier instead of an LLM supervisor, avoiding infinite loops common in multi-agent architectures.

User Query
│
▼
Intent Classifier
│
├── general    → Direct LLM response
├── sql_only   → SQL query → Formatted response
└── analysis   → SQL query → Analysis → (Chart) → (PDF) → (Email)

## Project Structure

```
analyst-react-agent/
│
├── data/                     # Database files
│   └── .gitkeep
│
├── outputs/                  # Generated files (charts, PDFs, CSVs)
│   └── .gitkeep
│
├── scripts/
│   └── create_database.py    # Database setup script
│
├── src/
│   ├── config.py             # LLM and environment setup
│   ├── state.py              # LangGraph state definition
│   ├── tools.py              # Agent tools (SQL, chart, PDF, email)
│   └── workflow.py           # Graph nodes and edges
│
├── .env.example
├── .gitignore
├── main.py                   # Application entry point
├── requirements.txt
└── README.md
```

## Getting Started

**1. Clone the repository**
```bash
git clone https://github.com/your-username/analyst-react-agent
cd analyst-react-agent
```

**2. Create and activate virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
DEEPSEEK_API_KEY=your_key_here
EMAIL_REMETENTE=your_email@gmail.com
EMAIL_SENHA=your_app_password
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=analyst-react-agent

**5. Create the database**
```bash
python scripts/create_database.py
```

**6. Run the agent**
```bash
python main.py
```

## Usage Examples

📝 Query: Who was the top seller in March 2024?
→ SQL query + formatted response
📝 Query: Analyze Q1 2024 sales and generate a PDF report
→ SQL query + analysis + PDF
📝 Query: Generate a bar chart of sales by category
→ SQL query + chart
📝 Query: Analyze revenue by region and send to email@example.com
→ SQL query + analysis + PDF + email

## Stack

| Tool | Purpose |
|------|---------|
| LangGraph | Agent flow orchestration |
| LangChain | LLM integration |
| DeepSeek | Language model |
| SQLite + Pandas | Database and data manipulation |
| Plotly | Chart generation |
| ReportLab | PDF generation |

## Key Design Decisions

**Deterministic intent classifier over LLM supervisor** — The original 3-agent architecture (SQL consultant + analyst + supervisor) caused infinite loops where the supervisor would repeatedly call agents unnecessarily. Replacing it with a rule-based classifier with LLM fallback made the flow predictable and debuggable.

**LangSmith observability** — Tracing every LLM call, tool invocation, and graph transition through LangSmith was essential for debugging. Without it, silent failures inside `except` blocks and unexpected LLM outputs would have been nearly impossible to track down. Enabling tracing is a first-class concern, not an afterthought.

## License

MIT
