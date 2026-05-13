from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
load_dotenv()

from src.workflow import workflow
import uuid

print("🤖 Sistema de Análise de Vendas")
print("=" * 50)
print("Digite 'sair' para encerrar ou 'nova conversa' para resetar o histórico.")
print("=" * 50)

# thread_id identifica a sessão — mesmo id = mesma memória
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

user_query = input("\n📝 Digite sua pergunta: ")

while user_query.lower() != "sair":
    if user_query.lower() == "nova conversa":
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        print("🔄 Nova conversa iniciada.")
        user_query = input("\n📝 Digite sua pergunta: ")
        continue

    try:
        resultado = workflow.invoke(
    {"messages": [HumanMessage(content=user_query)]},
    config=config
)
        
        print("\n" + "=" * 50)
        print("📌 RESPOSTA:")
        print("=" * 50)
        
        if resultado.get("final_answer"):
            print(resultado["final_answer"])
        
        if resultado.get("csv_path"):
            print(f"\n📁 CSV: {resultado['csv_path']}")
        if resultado.get("graph_path"):
            print(f"\n📊 Gráfico: {resultado['graph_path']}")
        if resultado.get("report_path"):
            print(f"\n📄 Relatório: {resultado['report_path']}")
        if resultado.get("email_sent"):
            print(f"\n📧 Email enviado com sucesso!")
        if resultado.get("error"):
            print(f"\n⚠️ Erro: {resultado['error']}")
            
    except Exception as e:
        print(f"\n❌ Erro no workflow: {e}")
    
    print("\n" + "-" * 50)
    user_query = input("\n📝 Digite sua pergunta: ")

print("\n👋 Até logo!")