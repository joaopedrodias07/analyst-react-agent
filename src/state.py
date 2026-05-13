from typing import TypedDict, List, Optional, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class SalesState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # acumula entre turnos
    user_query: str
    intention: str
    
    # Tudo abaixo é resetado a cada turno no classify_intention
    sql_result: Optional[str]
    csv_path: Optional[str]
    formatted_data: Optional[str]
    graph_path: Optional[str]
    report_path: Optional[str]
    email_sent: Optional[bool]
    final_answer: Optional[str]
    error: Optional[str]