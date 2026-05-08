
from dotenv import load_dotenv
load_dotenv()

from src.workflow import workflow

print("🤖 Sistema de Análise de Vendas")
print("=" * 50)
print("Exemplos:")
print("  • 'Quanto vendeu em janeiro?' → consulta SQL")
print("  • 'Analise as vendas do trimestre' → SQL + análise")
print("  • 'Gere um relatório em PDF' → SQL + análise + PDF")
print("  • 'sair' → encerrar")
print("=" * 50)

user_query = input("\n📝 Digite sua pergunta: ")

while user_query.lower() != "sair":
    try:
        resultado = workflow.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })
        
        print("\n" + "=" * 50)
        print("📌 RESPOSTA:")
        print("=" * 50)
        
        if resultado.get("final_answer"):
            print(resultado["final_answer"])
        
        # Info adicional
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