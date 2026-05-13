import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential
import time 
from langchain_openai import ChatOpenAI

load_dotenv()
os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "false")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "analyst-react-agent")

llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.1,
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def invoke_with_fallback(prompt: str, max_retries: int = 3) -> str:
    """
    Invoca o LLM com retry manual e fallback.
    Se todas as tentativas falharem, retorna None.
    """
    for tentativa in range(max_retries):
        try:
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"⚠️ Tentativa {tentativa + 1}/{max_retries} falhou: {e}")
            if tentativa < max_retries - 1:
                time.sleep(2 ** tentativa)  # backoff exponencial
            else:
                print(f"❌ Todas as tentativas falharam.")
                return None

'''
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


from langchain_groq import ChatGroq
llm = ChatGoogleGenerativeAI(
model="llama-3.3-70b-versatile",
temperature=0.2,
google_api_key= os.getenv("GROQ_API_KEY")
)
'''