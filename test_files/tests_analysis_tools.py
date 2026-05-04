from src.tools.database_tools import consultar_sql
from src.tools.analysis_tools import formatar_dados, gerar_grafico

# Pega dados reais do banco
dados = consultar_sql.invoke({
    "query": """
        SELECT d.nome, SUM(f.valor_total) as total_vendas
        FROM fato_vendas f
        JOIN dim_produtos d ON f.id_produto = d.id_produto
        GROUP BY d.nome
        ORDER BY total_vendas DESC
    """
})

# Teste 1: formatar dados
print("=== FORMATAR DADOS ===")
print(formatar_dados.invoke({"dados_json": dados}))

# Teste 2: gerar gráfico
print("\n=== GERAR GRÁFICO ===")
print(gerar_grafico.invoke({
    "dados_json": dados,
    "tipo": "barras",
    "titulo": "Total de Vendas por Produto",
    "eixo_x": "nome",
    "eixo_y": "total_vendas"
}))