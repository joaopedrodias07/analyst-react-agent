# src/graph/state.py
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Query original do usuário — nunca muda durante o fluxo
    pergunta: str
    
    # Histórico de mensagens — add_messages acumula em vez de sobrescrever
    messages: Annotated[list, add_messages]
    
    # Resultado do SQL Agent — JSON bruto
    dados_json: str
    
    # Resultado do Analyst Agent — análise em texto
    analise: str
    
    # Caminhos dos arquivos gerados
    grafico_path: str
    relatorio_path: str
    
    # Controle de fluxo — supervisor define quem age a seguir
    proximo_agente: str
    
    # Erro em qualquer etapa
    erro: str | None