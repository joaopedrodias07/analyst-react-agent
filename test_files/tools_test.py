# test_files/tools_test.py
from src.tools import (
    consultar_sql,
    exportar_csv,
    formatar_dados,
    gerar_grafico,
    gerar_relatorio,
    enviar_email
)
import os
from dotenv import load_dotenv
load_dotenv()

# ── TESTE 1: consultar_sql ────────────────────────────────
print("=== TESTE 1: consultar_sql ===")
resultado = consultar_sql.invoke({
    "query": """
        SELECT d.nome, SUM(f.valor_total) as total_vendas
        FROM fato_vendas f
        JOIN dim_produtos d ON f.id_produto = d.id_produto
        GROUP BY d.nome
        ORDER BY total_vendas DESC
    """
})
print(resultado)

# ── TESTE 2: exportar_csv ─────────────────────────────────
print("\n=== TESTE 2: exportar_csv ===")
resultado = exportar_csv.invoke({
    "dados_json": resultado,
    "nome_arquivo": "teste_produtos"
})
print(resultado)

# ── TESTE 3: formatar_dados ───────────────────────────────
print("\n=== TESTE 3: formatar_dados ===")
dados = consultar_sql.invoke({
    "query": "SELECT nome, categoria, preco_unitario FROM dim_produtos"
})
resultado = formatar_dados.invoke({"dados_json": dados})
print(resultado)

# ── TESTE 4: gerar_grafico ────────────────────────────────
print("\n=== TESTE 4: gerar_grafico ===")
dados = consultar_sql.invoke({
    "query": """
        SELECT v.nome AS vendedor, SUM(f.valor_total) AS faturamento
        FROM fato_vendas f
        JOIN dim_vendedores v ON f.id_vendedor = v.id_vendedor
        GROUP BY v.nome
        ORDER BY faturamento DESC
    """
})
resultado = gerar_grafico.invoke({
    "dados_json": dados,
    "tipo": "barras",
    "titulo": "Faturamento por Vendedor 2024",
    "eixo_x": "vendedor",
    "eixo_y": "faturamento"
})
print(resultado)

# ── TESTE 5: gerar_relatorio ──────────────────────────────
print("\n=== TESTE 5: gerar_relatorio ===")
grafico_path = resultado  
grafico_path = grafico_path.replace("Gráfico salvo em: ", "")

resultado = gerar_relatorio.invoke({
    "analise": "Carla Mendes foi a melhor vendedora de 2024 com R$ 2.376.670,72.",
    "titulo": "Relatório de Vendas 2024",
    "grafico_path": grafico_path
})
print(resultado)

destinatario = os.getenv("EMAIL_DESTINATARIO")
# ── TESTE 6: enviar_email ─────────────────────────────────
print("\n=== TESTE 6: enviar_email ===")
resultado = enviar_email.invoke({
    "destinatario": destinatario,
    "assunto": "Teste do sistema",
    "corpo": "Email de teste do analyst-react-agent.",
})
print(resultado)