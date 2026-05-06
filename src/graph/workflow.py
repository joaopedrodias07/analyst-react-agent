# src/graph/workflow.py
from langgraph.graph import StateGraph, START, END
from src.graph.state import AgentState
from src.agents.sql_agent import sql_agent
from src.agents.analyst_agent import analyst_agent
from src.config import llm
from langchain_core.messages import HumanMessage, SystemMessage

'''
# ── NÓS PLACEHOLDER ──────────────────────────────────────

def node_supervisor(state: AgentState) -> dict:
    """Supervisor — decide qual agente chamar."""
    return {"proximo_agente": "fim"}

def node_sql_agent(state: AgentState) -> dict:
    """SQL Agent."""
    return {}

def node_analyst_agent(state: AgentState) -> dict:
    """Analyst Agent."""
    return {}

def roteador(state: AgentState) -> str:
    return state["proximo_agente"]

# ── MONTAGEM ──────────────────────────────────────────────

def criar_grafo():
    grafo = StateGraph(AgentState)

    grafo.add_node("supervisor", node_supervisor)
    grafo.add_node("sql_agent", node_sql_agent)
    grafo.add_node("analyst_agent", node_analyst_agent)

    grafo.add_edge(START, "supervisor")

    grafo.add_conditional_edges(
        "supervisor",
        roteador,
        {
            "sql_agent": "sql_agent",
            "analyst_agent": "analyst_agent",
            "fim": END
        }
    )

    grafo.add_edge("sql_agent", "supervisor")
    grafo.add_edge("analyst_agent", "supervisor")

    return grafo.compile()

workflow = criar_grafo()
'''
from src.agents.sql_agent import sql_agent
from src.agents.analyst_agent import analyst_agent
from src.config import llm
from langchain_core.messages import HumanMessage, SystemMessage

def node_sql_agent(state: AgentState) -> dict:
    """
    Nó do SQL Agent no grafo.
    Recebe a pergunta do usuário via state, invoca o SQL Agent
    que consulta o banco de dados, gera csv e salva o resultado JSON no state.
    """
    resposta = sql_agent.invoke({
        "messages": [{"role": "user", "content": f"""
            {state["pergunta"]}
            IMPORTANTE: retorne APENAS o JSON bruto dos dados, sem formatação.
        """}]
    })
    content = resposta["messages"][-1].content
    dados_json = content[0]["text"] if isinstance(content, list) else content
    return {"dados_json": dados_json}


def node_analyst_agent(state: AgentState) -> dict:
    """
    Nó do Analyst Agent no grafo.
    Recebe os dados JSON do state gerados pelo SQL Agent,
    invoca o Analyst Agent que gera insights, gráficos,
    relatórios, pdf e envia emails conforme solicitado.
    """
    resposta = analyst_agent.invoke({
        "messages": [{"role": "user", "content": f"""
            Pedido original: {state["pergunta"]}
            Dados em JSON: {state["dados_json"]}
            Use suas tools para completar o pedido.
        """}]
    })
    content = resposta["messages"][-1].content
    analise = content[0]["text"] if isinstance(content, list) else content
    return {"analise": analise}


def node_supervisor(state: AgentState) -> dict:
    """
    Nó do Supervisor no grafo.
    Analisa o estado atual e decide qual agente invocar a seguir
    ou se o fluxo deve ser encerrado. É o ponto central de 
    orquestração do sistema multiagente.
    """
    
    passos = state.get("passos", 0) + 1
    if passos > 5:
        return {"proximo_agente": "fim", "passos": passos}
    
    system_prompt = """Você é o supervisor de um sistema multiagente de análise financeira.
Seu papel é orquestrar o fluxo de trabalho decidindo qual agente deve agir a seguir.

## Estado Atual do Fluxo
- Dados coletados: {dados_status}
- Análise gerada: {analise_status}  
- Passos executados: {passos}/5

## Regras de Decisão

## Regras de Decisão

Responda "sql_agent" quando:
- A resposta da query exige consulta no banco de dados e/ou exportação em csv e os dados ainda não foram coletados (dados_json VAZIO).

Responda "analyst_agent" quando:
- A query do usuário exige alguma forma de análise(algo alem de só retornar os valores da consulta), visualização(graficos), geração de relatório, pdf ou envio de email E os dados já foram coletados (dados_json PREENCHIDO) mas a análise ainda não foi gerada (analise VAZIA).


Responda "fim" quando:
-A pergunta não exigia nenhuma das ferramentas disponíveis (consulta, exportação para csv,análise, visualização, relatório, pdf, email) e só a respota em texto já resolve o pedido do usuário
- A pergunta exigia apenas consulta e essa consulta já foi realizada (dados_json PREENCHIDO)
- A pergunta exigia alguma forma de análise, visualização, relatório, pdf ou email e os dados já foram coletados (dados_json PREENCHIDO) e a análise já foi gerada (analise PREENCHIDA)
- Não há mais ações necessárias

## Importante
- Responda APENAS com uma palavra: sql_agent, analyst_agent ou fim
- Nunca repita um agente que já foi executado com sucesso
- Em caso de dúvida, prefira "fim" para evitar loops"""

    messages = [
        SystemMessage(content=system_prompt.format(
            dados_status="PREENCHIDO" if state.get("dados_json") else "VAZIO",
            analise_status="PREENCHIDA" if state.get("analise") else "VAZIA",
            passos=state.get("passos", 0)
        )),
        HumanMessage(content=f"Pergunta do usuário: {state['pergunta']}")
    ]
    
    decisao = llm.invoke(messages)
    content = decisao.content
    proximo = content[0]["text"] if isinstance(content, list) else content
    proximo = proximo.strip().lower()
    
    if proximo not in ["sql_agent", "analyst_agent", "fim"]:
        proximo = "fim"
    
    return {"proximo_agente": proximo, "passos": passos}

def roteador(state: AgentState) -> str:
    """Define para onde o grafo vai baseado na decisão do supervisor."""
    return state["proximo_agente"]


# ── MONTAGEM DO GRAFO ─────────────────────────────────────

def criar_grafo():
    grafo = StateGraph(AgentState)

    grafo.add_node("supervisor", node_supervisor)
    grafo.add_node("sql_agent", node_sql_agent)
    grafo.add_node("analyst_agent", node_analyst_agent)

    grafo.add_edge(START, "supervisor")

    grafo.add_conditional_edges(
        "supervisor",
        roteador,
        {
            "sql_agent": "sql_agent",
            "analyst_agent": "analyst_agent",
            "fim": END
        }
    )

    grafo.add_edge("sql_agent", "supervisor")
    grafo.add_edge("analyst_agent", "supervisor")

    return grafo.compile()


workflow = criar_grafo()