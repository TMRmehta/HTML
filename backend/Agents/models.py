import os, sys
from pydantic import BaseModel
from typing import Optional, List, Any, Literal

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class ChatRequest(BaseModel):
    question:str

class ChatAPIRequest(BaseModel):
    user_id:str
    chat_id:str
    question:str

class ChatAPIAnswer(BaseModel):
    user_id:str
    chat_id:str
    answer: str
    reasoning: Optional[List[Any]] = None
    sources: Optional[list[Any]] = None
    tools: Optional[list[Any]] = None
    type: Optional[Any] = None

class PatientChatResponse(BaseModel):
    answer:str
    reasoning: Optional[List[Any]] = None
    sources: Optional[List[Any]] = None
    return_status: Literal["success", "failed", "fallback"]

class ResearchChatResponse(BaseModel):
    answer:str
    reasoning: Optional[List[Any]] = None
    sources: Optional[List[Any]] = None
    return_status: Literal["success", "failed", "fallback"]

class ChatResponse(BaseModel):
    answer: str
    reasoning: Optional[List[Any]] = None
    sources: Optional[list[Any]] = None
    tools: Optional[list[Any]] = None
    type: Optional[Any] = None