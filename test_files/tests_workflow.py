# test_files/tests_grafo.py

from src.graph.workflow import workflow
'''
imagem = workflow.get_graph().draw_mermaid_png()

with open("outputs/grafo.png", "wb") as f:
    f.write(imagem)

print("Grafo salvo em outputs/grafo.png")
'''

user_query = input("Digite: ")
while user_query != "sair":
    try:
        resultado = workflow.invoke({
            "pergunta": user_query,
            "messages": [],
            "dados_json": "",
            "analise": "",
            "grafico_path": "",
            "relatorio_path": "",
            "proximo_agente": "",
            "erro": None,
            "passos": 0
        })
        
        print("\n=== RESPOSTA ===")
        print(resultado["analise"] or resultado["dados_json"])
        
    except Exception as e:
        print(f"Erro: {e}")
    
    user_query = input("\nDigite: ")