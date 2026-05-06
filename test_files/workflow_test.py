# test_files/workflow_test.py
from dotenv import load_dotenv
load_dotenv()

from src.workflow import workflow

user_query = input("Digite: ")
while user_query != "sair":
    try:
        resultado = workflow.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })
        print("\n=== RESPOSTA ===")
        print(resultado["messages"][-1].content)
    except Exception as e:
        print(f"Erro: {e}")

    user_query = input("\nDigite: ")