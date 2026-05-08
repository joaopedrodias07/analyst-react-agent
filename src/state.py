# src/graph/state.py
from typing import TypedDict, List, Optional, Any

class SalesState(TypedDict):
    messages: List[dict]                  # Histórico completo
    user_query: str                       # Query original do usuário
    intention: str                        # "general", "sql_only", "analysis"
    
    # Dados do SQL
    sql_result: Optional[str]             # JSON da consulta
    csv_path: Optional[str]               # Caminho do CSV exportado
    
    # Dados da Análise
    formatted_data: Optional[str]         # Texto formatado
    graph_path: Optional[str]             # Caminho do gráfico
    report_path: Optional[str]            # Caminho do PDF
    email_sent: bool                      # Flag de email enviado
    
    # Controle
    final_answer: Optional[str]           # Resposta final para o usuário
    error: Optional[str]                  # Mensagem de erro, se houver