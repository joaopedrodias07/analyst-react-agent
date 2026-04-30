import sqlite3
import pandas as pd
import json
import os
from langchain_core.tools import tool
from io import StringIO

DB_PATH = "data/vendas.db"


@tool
def consultar_sql(query: str) -> str:
    """
    Executa uma query SQL no banco de dados financeiro e retorna os resultados.
    Use para buscar dados de vendas, produtos, clientes e vendedores.

    O banco segue um modelo estrela com as tabelas:
    - fato_vendas: id_venda, id_produto, id_cliente, id_vendedor, data, quantidade, valor_total, desconto
    - dim_produtos: id_produto, nome, categoria, preco_unitario
    - dim_clientes: id_cliente, nome, sexo, idade, email, regiao
    - dim_vendedores: id_vendedor, nome, email, regiao, cargo

    Args:
        query: Query SQL válida para SQLite
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return "A consulta não retornou dados."

        return df.to_json(orient="records")

    except Exception as e:
        return f"ERRO ao executar query: {str(e)}"


@tool
def exportar_csv(dados_json: str, nome_arquivo: str) -> str:
    """
    Converte dados JSON para CSV e salva na pasta outputs/.
    Use APÓS consultar_sql quando o usuário pedir para exportar os dados.

    Args:
        dados_json: resultado da tool consultar_sql em formato JSON
        nome_arquivo: nome do arquivo sem extensão, ex: 'vendas_q1'
    """
    try:
        os.makedirs("outputs", exist_ok=True)

        print(f"TIPO: {type(dados_json)}")
        print(f"VALOR: {dados_json[:100]}")
        df = pd.read_json(StringIO(dados_json))
        caminho = f"outputs/{nome_arquivo}.csv"
        df.to_csv(caminho, index=False)
        return f"CSV exportado com sucesso: {caminho}"

    except Exception as e:
        return f"ERRO ao exportar CSV: {str(e)}"
