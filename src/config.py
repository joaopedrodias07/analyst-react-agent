import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Trocarei pelo modelo do groq depois de todos os testes(groq tem um limite menor de tokens)
# from langchain_groq import ChatGroq
# llm = ChatGoogleGenerativeAI(
# model="llama-3.3-70b-versatile",
# temperature=0,
# google_api_key= os.getenv("GROQ_API_KEY")
# )
