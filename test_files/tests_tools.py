from src.tools.database_tools import consultar_sql, exportar_csv

# Teste 1: consulta simples
print("=== CONSULTA ===")
resultado = consultar_sql.invoke({
    "query": "SELECT nome, categoria, preco_unitario FROM dim_produtos"
})
print(resultado)

# Teste 2: exporta CSV
print("\n=== EXPORTAR CSV ===")
resultado = exportar_csv.invoke({
    "dados_json": consultar_sql.invoke({
        "query": "SELECT * FROM fato_vendas LIMIT 10"
    }),
    "nome_arquivo": "teste_vendas"
})
print(resultado)
