
from typing import Literal
from langgraph.graph import StateGraph, END
from src.config import llm, invoke_with_fallback
from src.state import SalesState
from src.tools import (
    consultar_sql,
    exportar_csv,
    formatar_dados,
    gerar_grafico,
    gerar_relatorio,
    enviar_email
)
import json
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# ═══════════════════════════════════════════════════════════
# CLASSIFICADOR DE INTENÇÃO
# ═══════════════════════════════════════════════════════════

CLASSIFIER_PROMPT = """
Você é um classificador de intenção para um sistema de análise de vendas.

Classifique a mensagem do usuário em UMA das três categorias:

1. "general" - Perguntas que NÃO precisam de dados do banco.
   Exemplos: "o que você faz?", "quais ferramentas?", "bom dia", "obrigado"

2. "sql_only" - Precisa de dados mas NÃO pede análise/insights/gráficos/relatórios.
   Exemplos: "quanto vendeu em janeiro?", "quem foi o melhor vendedor em outubro?", 
   "exporta pra CSV", "lista os produtos mais vendidos"

3. "analysis" - Pede análise, insights, tendências, gráficos, relatórios, PDF ou email.
   PALAVRAS-CHAVE: análise, analisar, insight, tendência, padrão, gráfico, 
   relatório, PDF, email, recomendação, sugestão, diagnóstico, avaliação
   Exemplos: "analise as vendas do trimestre", "faça uma análise da equipe",
   "gere um relatório com gráfico", "me mande por email"

REGRAS CRÍTICAS:
- Se contém "análise", "analise", "analisar" → SEMPRE é "analysis"
- "melhor", "pior", "maior", "menor" são consultas SQL → "sql_only"
- "analysis" tem prioridade máxima: se aparece palavra de análise, ignore outras

Mensagem do usuário: {user_msg}

Responda APENAS com JSON: {{"intention": "<categoria>", "reasoning": "<breve>"}}
"""
def fallback_classification(user_msg: str) -> str:
    """Classificação por regras quando o LLM falha."""
    msg = user_msg.lower()
    
    # 1. Analysis (MAIOR PRIORIDADE)
    analysis_words = [
        "análise", "analise", "analisar", "analisa",
        "insight", "tendência", "tendencia", "padrão", "padrao",
        "gráfico", "grafico", "visualização", "visualizacao", "plot",
        "relatório", "relatorio", "pdf",
        "email", "e-mail", "enviar",
        "recomendação", "recomendacao", "sugestão", "sugestao",
        "diagnóstico", "diagnostico", "avaliação", "avaliacao"
    ]
    if any(word in msg for word in analysis_words):
        return "analysis"
    
    # 2. SQL Only
    sql_patterns = [
        "qual", "quais", "quem", "quando", "onde", "quanto", "quantos",
        "melhor", "pior", "maior", "menor", "top", "ranking",
        "vendas", "vendedor", "cliente", "produto", "categoria", "região", "regiao",
        "faturamento", "receita", "lucro", "desconto",
        "exportar", "csv", "tabela", "dados", "consulta", "query",
        "mês", "mes", "trimestre", "semestre", "ano", "semana",
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        "2024", "2025", "2026"
    ]
    if any(word in msg for word in sql_patterns):
        return "sql_only"
    
    # 3. Geral
    return "general"

def classify_intention(state: SalesState) -> SalesState:
    last_message = state["messages"][-1]
    user_msg = last_message.content
    state["user_query"] = user_msg

    # Reseta campos voláteis a cada novo turno
    state["sql_result"] = None
    state["csv_path"] = None
    state["formatted_data"] = None
    state["graph_path"] = None
    state["report_path"] = None
    state["email_sent"] = None
    state["final_answer"] = None
    state["error"] = None

    prompt = CLASSIFIER_PROMPT.format(user_msg=user_msg)
    response = invoke_with_fallback(prompt)

    if response:
        try:
            result = json.loads(response)
            state["intention"] = result["intention"]
            print(f"🤖 LLM classificou como: {state['intention']}")
            return state
        except:
            pass

    state["intention"] = fallback_classification(user_msg)
    print(f"⚠️ Fallback classificou como: {state['intention']}")
    return state

# ═══════════════════════════════════════════════════════════
# NÓS DO GRAFO
# ═══════════════════════════════════════════════════════════

def answer_general(state: SalesState) -> SalesState:
    # Monta histórico a partir dos objetos de mensagem
    historico = []
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            historico.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            historico.append({"role": "assistant", "content": msg.content})

    prompt = f"""Você é um assistente amigável de análise financeira.
Responda de forma útil, em português.

O sistema pode:
- Consultar banco de dados SQL de vendas
- Exportar dados para CSV
- Gerar gráficos (linha, barra, pizza, histograma)
- Criar relatórios em PDF
- Enviar relatórios por email

Histórico da conversa:
{historico}

Usuário: {state['user_query']}
"""
    response = llm.invoke(prompt)
    
    # Resposta salva como AIMessage no histórico
    state["messages"] = [AIMessage(content=response.content)]
    state["final_answer"] = response.content
    return state

import re

def clean_sql_query(text: str) -> str:
    """
    Remove blocos de markdown e extrai APENAS o SQL puro.
    """
    # Remove blocos ```sql ... ``` ou ``` ... ```
    # Padrão: ``` (opcionalmente 'sql') no início e ``` no final
    cleaned = re.sub(r'^```(?:sql)?\s*\n', '', text.strip())
    cleaned = re.sub(r'\n```\s*$', '', cleaned)
    
    # Garante que não restou nenhuma crase perdida
    cleaned = cleaned.replace('```', '')
    
    return cleaned.strip()

def run_sql_agent(state: SalesState) -> SalesState:
    """
    Executa consulta SQL e opcionalmente exporta CSV.
    Fluxo determinístico: gerar query → executar → (exportar se pedido)
    """
    # 1. Gerar query SQL
    sql_prompt = f"""
   Você é um especialista SQL. Gere APENAS a query SQL para a pergunta abaixo.

    IMPORTANTE: 
    - Retorne SOMENTE o código SQL puro
    - NÃO use blocos de código markdown (sem ```sql ou ```)
    - NÃO inclua explicações ou comentários
    - Apenas a query SQL, nada mais

    Tabelas disponíveis:
    - fato_vendas: id_venda, id_produto, id_cliente, id_vendedor, data, quantidade, valor_total, desconto
    - dim_produtos: id_produto, nome, categoria, preco_unitario
    - dim_clientes: id_cliente, nome, sexo, idade, email, regiao
    - dim_vendedores: id_vendedor, nome, email, regiao, cargo
    
    Gere APENAS a query SQL para: {state['user_query']}
    Regras:
    - Use JOINs quando precisar de dados de múltiplas tabelas
    - Para "melhor/pior/maior/menor", use ORDER BY + LIMIT
    - Nunca use DELETE, UPDATE, DROP
    - Retorne APENAS o código SQL, sem explicações
    """
    
    query_response = invoke_with_fallback(sql_prompt)
    if not query_response:
        state["final_answer"] = "❌ Não consegui gerar a consulta SQL. Tente novamente."
        state["error"] = "Falha ao gerar query"
        return state
    
    query = clean_sql_query(query_response)
    print(f"📊 Query gerada: {query}")
    
    # 2. Executar query
    result = consultar_sql.invoke({"query": query})
    state["sql_result"] = result
    
    if "ERRO" in result:
        state["final_answer"] = f"❌ {result}"
        state["error"] = result
        return state
    
    # 3. Exportar CSV se pedido
    if any(word in state["user_query"].lower() for word in ["csv", "exportar", "baixar", "download"]):
        csv_result = exportar_csv.invoke({
            "dados_json": result,
            "nome_arquivo": "consulta"
        })
        state["csv_path"] = csv_result.replace("CSV exportado com sucesso: ", "")
    
    return state


def run_analyst_agent(state: SalesState) -> SalesState:
    """
    Executa análise de forma determinística:
    1. Formatar dados
    2. Gerar análise textual
    3. Gráfico (se pedido)
    4. Relatório PDF (se pedido)
    5. Email (se pedido)
    """
    user_query = state["user_query"].lower()

    # Detecta se o usuário pediu APENAS gráfico (sem análise, relatório, etc.)
    graph_keywords = ["gráfico", "grafico", "visualização", "visualizacao", "plot", "barras", "pizza", "linha"]
    analysis_keywords = ["análise", "analise", "analisar", "insight", "tendência", "tendencia",
                         "recomendação", "recomendacao", "relatório", "relatorio", "pdf"]

    pediu_grafico = any(word in user_query for word in graph_keywords)
    pediu_analise = any(word in user_query for word in analysis_keywords)
    so_grafico = pediu_grafico and not pediu_analise

    # 1. Formatar dados (SEMPRE)
    formatted = formatar_dados.invoke({"dados_json": state["sql_result"]})
    state["formatted_data"] = formatted
    print("📋 Dados formatados")

    # 2. Gerar análise textual (só se pediu análise OU não pediu só gráfico)
    if not so_grafico:
        analysis_prompt = f"""
        Você é um analista financeiro sênior. Analise os dados abaixo:
        
        {formatted}
        
        Pedido do usuário: {state['user_query']}
        
        Forneça:
        1. RESUMO EXECUTIVO (2-3 linhas)
        2. PRINCIPAIS INSIGHTS (3-5 pontos)
        3. RECOMENDAÇÕES PRÁTICAS
        
        Formate valores como R$ X.XXX,XX.
        NÃO inclua endereços de email, nomes de destinatários ou cabeçalhos de carta no texto.
        """
        analysis_response = invoke_with_fallback(analysis_prompt)
        if not analysis_response:
            state["final_answer"] = "❌ Falha ao gerar análise. Os dados estão disponíveis."
            state["error"] = "Falha na análise"
            return state

        state["analysis_text"] = analysis_response
        print("📝 Análise gerada")
    else:
        analysis_response = None
        print("📊 Modo gráfico apenas — análise textual pulada")

    # 3. Gráfico (se pedido)
    if pediu_grafico:
        try:
            colunas = list(json.loads(state["sql_result"])[0].keys())
        except Exception:
            colunas = []

        graph_prompt = f"""Retorne APENAS um objeto JSON, sem explicações, sem código Python, sem markdown.

Formato exigido (preencha com os valores corretos):
{{"tipo": "barras", "eixo_x": "nome_coluna", "eixo_y": "nome_coluna", "titulo": "titulo do grafico"}}

Tipos válidos: linha, barras, pizza, histograma
Colunas disponíveis: {colunas}
Pedido do usuário: {state['user_query']}

JSON:"""

        graph_response = invoke_with_fallback(graph_prompt)
        if graph_response:
            try:
                cleaned = re.sub(r'^```(?:json)?\s*\n?', '', graph_response.strip())
                cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
                graph_params = json.loads(cleaned)
                graph_result = gerar_grafico.invoke({
                    "dados_json": state["sql_result"],
                    "tipo": graph_params["tipo"],
                    "titulo": graph_params["titulo"],
                    "eixo_x": graph_params["eixo_x"],
                    "eixo_y": graph_params["eixo_y"]
                })
                if "Gráfico salvo em:" in graph_result:
                    state["graph_path"] = graph_result.replace("Gráfico salvo em: ", "")
                    print(f"📊 Gráfico gerado: {state['graph_path']}")
                else:
                    print(f"⚠️ Falha ao gerar gráfico: {graph_result}")
            except Exception as e:
                print(f"⚠️ Falha ao parsear parâmetros do gráfico: {e}")
                print(f"   Resposta recebida: {graph_response[:200]}")

    # 4. Gerar título profissional para o relatório/email
    titulo = state['user_query'][:50]  # fallback
    report_keywords = ["relatório", "relatorio", "pdf"]
    email_keywords = ["email", "e-mail", "enviar por email", "enviar email"]
    pediu_relatorio = any(word in user_query for word in report_keywords)
    pediu_email = any(word in user_query for word in email_keywords)

    if pediu_relatorio or pediu_email:
        titulo_prompt = f"""Crie um título profissional curto (máximo 8 palavras) para um relatório sobre:
{state['user_query']}

Título:"""
        titulo_response = invoke_with_fallback(titulo_prompt)
        if titulo_response:
            titulo = titulo_response.strip().strip('"')
        print(f"📌 Título gerado: {titulo}")

    # 5. Relatório PDF (se pedido)
    if pediu_relatorio:
        report_result = gerar_relatorio.invoke({
            "analise": analysis_response or "",
            "titulo": titulo,
            "grafico_path": state.get("graph_path", "")
        })
        if "Relatório salvo em:" in report_result:
            state["report_path"] = report_result.replace("Relatório salvo em: ", "")
            print(f"📄 Relatório gerado: {state['report_path']}")
        else:
            print(f"⚠️ Falha ao gerar relatório: {report_result}")

    # 6. Email (se pedido)
    if pediu_email:
        email_extract_prompt = f"""Extraia APENAS o endereço de email desta mensagem.
Se não houver email, retorne exatamente: nao_encontrado

Mensagem: {state['user_query']}

Email:"""
        email_response = invoke_with_fallback(email_extract_prompt)

        if email_response and "nao_encontrado" not in email_response.lower():
            match = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', email_response)
            if match:
                destinatario = match.group(0)

                # Gera corpo de email profissional e curto
                email_body_prompt = f"""Escreva um corpo de email profissional e curto (3-4 linhas)
informando que o relatório de análise de vendas está anexo.
Não inclua saudação inicial nem assinatura.
Tema do relatório: {state['user_query']}

Email:"""
                corpo_email = invoke_with_fallback(email_body_prompt) or \
                    "Segue em anexo o relatório de análise de vendas solicitado."

                email_result = enviar_email.invoke({
                    "destinatario": destinatario,
                    "assunto": titulo,
                    "corpo": corpo_email,
                    "anexo_path": state.get("report_path", "")
                })
                state["email_sent"] = "sucesso" in email_result.lower()
                print(f"📧 Email {'enviado' if state['email_sent'] else 'falhou'}: {destinatario}")
            else:
                print(f"⚠️ Endereço de email não encontrado. Resposta LLM: {email_response}")
                state["email_sent"] = False
        else:
            print("⚠️ Usuário pediu email mas não forneceu endereço.")
            state["email_sent"] = False

    # Resposta final
    if so_grafico:
        path = state.get("graph_path", "")
        state["final_answer"] = f"📊 Gráfico gerado: {path}" if path else "❌ Não foi possível gerar o gráfico."
    else:
        state["final_answer"] = analysis_response

    return state


def prepare_final_response(state: SalesState) -> SalesState:
    if state.get("final_answer"):
        # Salva resposta final como AIMessage no histórico
        state["messages"] = [AIMessage(content=state["final_answer"])]
        return state
    
    if state["intention"] == "sql_only":
        dados = state.get("sql_result", "Sem dados")
        state["final_answer"] = f"📊 **Resultado da consulta:**\n\n{dados}"
    else:
        state["final_answer"] = "✅ Processo concluído."
    
    state["messages"] = [AIMessage(content=state["final_answer"])]
    return state


# ═══════════════════════════════════════════════════════════
# ROTEADORES (DETERMINÍSTICOS)
# ═══════════════════════════════════════════════════════════

def route_after_classification(state: SalesState) -> Literal["answer_general", "run_sql_agent"]:
    """Roteia baseado na intenção."""
    if state["intention"] == "general":
        return "answer_general"
    else:
        return "run_sql_agent"  # sql_only ou analysis = precisa de dados


def route_after_sql(state: SalesState) -> Literal["run_analyst_agent", "prepare_final_response"]:
    """Após SQL, decide se vai para análise ou resposta final."""
    if state.get("error"):
        return "prepare_final_response"  # Se deu erro, vai direto pro fim
    
    if state["intention"] == "analysis":
        return "run_analyst_agent"
    else:
        return "prepare_final_response"  # sql_only: já podemos responder


# ═══════════════════════════════════════════════════════════
# CONSTRUÇÃO DO GRAFO
# ═══════════════════════════════════════════════════════════

def create_workflow():
    workflow = StateGraph(SalesState)
    
    # Nós
    workflow.add_node("classify_intention", classify_intention)
    workflow.add_node("answer_general", answer_general)
    workflow.add_node("run_sql_agent", run_sql_agent)
    workflow.add_node("run_analyst_agent", run_analyst_agent)
    workflow.add_node("prepare_final_response", prepare_final_response)
    
    # Entry point
    workflow.set_entry_point("classify_intention")
    
    # Classificação → resposta geral OU consulta SQL
    workflow.add_conditional_edges(
        "classify_intention",
        route_after_classification,
        {
            "answer_general": "answer_general",
            "run_sql_agent": "run_sql_agent"
        }
    )
    
    # SQL → análise OU resposta final
    workflow.add_conditional_edges(
        "run_sql_agent",
        route_after_sql,
        {
            "run_analyst_agent": "run_analyst_agent",
            "prepare_final_response": "prepare_final_response"
        }
    )
    
    # Análise → resposta final
    workflow.add_edge("run_analyst_agent", "prepare_final_response")
    
    # Respostas → fim
    workflow.add_edge("answer_general", END)
    workflow.add_edge("prepare_final_response", END)
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Instância do workflow
workflow = create_workflow()