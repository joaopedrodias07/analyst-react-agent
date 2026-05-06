# src/graph/workflow.py
from langgraph_supervisor import create_supervisor
from src.config import llm
from src.subagents import sql_agent, analyst_agent

SUPERVISOR_PROMPT = """
Você é o supervisor de um sistema multiagente de análise financeira.
Sua função é delegar tarefas para os agentes especializados corretos.

## Agentes Disponíveis
- **sql_agent**: especialista em consultas SQL e exportação de dados
- **analyst_agent**: especialista em análise, gráficos, relatórios e email

## Regras de Delegação
- Sempre delegue para sql_agent primeiro quando precisar de dados do banco
- Delegue para analyst_agent quando precisar de análise, gráficos, relatórios ou email
- Para perguntas simples que só precisam de dados, sql_agent já resolve sozinho
"""

workflow = create_supervisor(
    [sql_agent, analyst_agent],
    model=llm,
    prompt=SUPERVISOR_PROMPT
).compile()