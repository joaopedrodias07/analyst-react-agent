from src.agents.sql_agent import sql_agent
from src.config import extrair_texto
import time
'''
resposta = sql_agent.invoke({
    "messages": [{"role": "user", "content": "Qual o produto mais vendido em outubro de 2024?"}]
})

print(extrair_texto(resposta))
'''


user_query = input('Digite: ') 
while user_query != 'sair':
    try:
        resposta = sql_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })
        print(extrair_texto(resposta))
    except Exception as e:
        print("Erro:", e)
        print("Tentando novamente...")
        time.sleep(3)
        continue

    user_query = input('Digite: ')
