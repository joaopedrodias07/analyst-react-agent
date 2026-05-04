# src/tools/analysis_tools.py
import os
import uuid
import pandas as pd
import plotly.express as px
from io import StringIO
from langchain_core.tools import tool

@tool
def formatar_dados(dados_json: str) -> str:
    """
    Formata dados JSON em texto estruturado para facilitar a análise.
    Use sempre antes de analisar os dados para ter uma visão completa.

    Args:
        dados_json: resultado da tool consultar_sql em formato JSON
    """
    try:
        df = pd.read_json(StringIO(dados_json))

        resumo  = f"Total de registros: {df.shape[0]}\n\n"
        resumo += f"Colunas disponíveis: {list(df.columns)}\n\n"
        resumo += f"Dados completos:\n{df.to_string()}\n\n"
        resumo += f"Estatísticas numéricas:\n{df.describe().to_string()}"

        return resumo

    except Exception as e:
        return f"ERRO ao formatar dados: {str(e)}"

@tool
def gerar_grafico(dados_json: str, tipo: str, titulo: str, eixo_x: str, eixo_y: str) -> str:
    """
    Gera um gráfico a partir dos dados fornecidos e salva em outputs/.
    Use quando o usuário pedir visualização ou análise gráfica.

    Tipos disponíveis:
    - 'linha': evolução ao longo do tempo
    - 'barras': comparação numérica entre categorias
    - 'pizza': proporção entre categorias
    - 'histograma': distribuição de uma variável

    Args:
        dados_json: resultado da tool consultar_sql em formato JSON
        tipo: tipo do gráfico ('linha', 'barras', 'pizza', 'histograma')
        titulo: título do gráfico
        eixo_x: coluna do DataFrame para o eixo X (ou 'names' no pizza)
        eixo_y: coluna do DataFrame para o eixo Y (ou 'values' no pizza)
    """
    try:
        os.makedirs("outputs", exist_ok=True)

        df = pd.read_json(StringIO(dados_json))

        # Decide o tipo de gráfico
        if tipo == "linha":
            fig = px.line(df, x=eixo_x, y=eixo_y, title=titulo)
        elif tipo == "barras":
            fig = px.bar(df, x=eixo_x, y=eixo_y, title=titulo)
        elif tipo == "pizza":
            fig = px.pie(df, names=eixo_x, values=eixo_y, title=titulo)
        elif tipo == "histograma":
            fig = px.histogram(df, x=eixo_x, title=titulo)
        else:
            return f"ERRO: tipo '{tipo}' não suportado. Use: linha, barras, pizza ou histograma."

        # Nome único para o arquivo
        nome_arquivo = f"outputs/grafico_{uuid.uuid4().hex[:8]}.png"
        fig.write_image(nome_arquivo)

        return f"Gráfico salvo em: {nome_arquivo}"

    except Exception as e:
        return f"ERRO ao gerar gráfico: {str(e)}"
    
@tool
def gerar_relatorio(analise: str, titulo: str, grafico_path: str = None) -> str:
    """
    Gera um relatório em PDF com a análise e opcionalmente um gráfico.
    Use quando o usuário pedir um relatório formal.

    Args:
        analise: texto com a análise gerada pelo agente
        titulo: título do relatório
        grafico_path: caminho do gráfico gerado (opcional)
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

        os.makedirs("outputs", exist_ok=True)
        nome_arquivo = f"outputs/relatorio_{uuid.uuid4().hex[:8]}.pdf"

        doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
        styles = getSampleStyleSheet()
        elementos = []

        # Título
        elementos.append(Paragraph(titulo, styles["Title"]))
        elementos.append(Spacer(1, 20))

        # Análise em texto
        for paragrafo in analise.split("\n"):
            if paragrafo.strip():
                elementos.append(Paragraph(paragrafo, styles["Normal"]))
                elementos.append(Spacer(1, 8))

        # Gráfico (se fornecido)
        if grafico_path and os.path.exists(grafico_path):
            elementos.append(Spacer(1, 20))
            elementos.append(Image(grafico_path, width=450, height=300))

        doc.build(elementos)
        return f"Relatório salvo em: {nome_arquivo}"

    except Exception as e:
        return f"ERRO ao gerar relatório: {str(e)}"
    
@tool
def enviar_email(destinatario: str, assunto: str, corpo: str, anexo_path: str = None) -> str:
    """
    Envia um email com ou sem anexo.
    Use SOMENTE quando o usuário pedir explicitamente para enviar por email.

    Args:
        destinatario: endereço de email do destinatário
        assunto: assunto do email
        corpo: corpo do email em texto
        anexo_path: caminho do arquivo para anexar (opcional)
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    try:
        remetente = os.getenv("EMAIL_REMETENTE")
        senha = os.getenv("EMAIL_SENHA")

        msg = MIMEMultipart()
        msg["From"] = remetente
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain"))

        # Anexa o arquivo se fornecido
        if anexo_path and os.path.exists(anexo_path):
            with open(anexo_path, "rb") as f:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(f.read())
                encoders.encode_base64(parte)
                parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(anexo_path)}")
                msg.attach(parte)

        # Envia via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, destinatario, msg.as_string())

        return f"Email enviado com sucesso para {destinatario}!"

    except Exception as e:
        return f"ERRO ao enviar email: {str(e)}"