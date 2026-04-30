from src.agents.sql_agent import sql_agent
from src.config import extrair_texto

resposta = sql_agent.invoke({
    "messages": [{"role": "user", "content": "Qual o produto mais vendido em outubro de 2024?"}]
})

print(extrair_texto(resposta))
