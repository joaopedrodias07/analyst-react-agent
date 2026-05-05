# test_files/tests_analyst_agent.py
from src.agents.sql_agent import sql_agent
from src.agents.analyst_agent import analyst_agent
from src.config import extrair_texto


  
user_query = input("Digite: ")
while user_query != "sair":
    try:
        # Passo 1: SQL Agent decide qual query fazer
        sql_resposta = sql_agent.invoke({
            "messages": [{"role": "user", "content": f"""
                {user_query}
                IMPORTANTE: retorne APENAS o JSON bruto dos dados, sem formatação.
            """}]
        })
        dados_json = extrair_texto(sql_resposta)

        # Passo 2: Analyst Agent recebe o JSON explicitamente
        analise = analyst_agent.invoke({
            "messages": [{"role": "user", "content": f"""
                Pedido original: {user_query}
                
                Dados em JSON para análise: 
                {dados_json}
                
                Use suas tools para completar o pedido.
            """}]
        })

        print(extrair_texto(analise))

    except Exception as e:
        print(f"Erro: {e}")

    user_query = input("\nDigite: ")
