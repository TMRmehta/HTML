from pydantic import BaseModel
from typing import List, Literal, Any, Optional

class ChatLookup(BaseModel):
    user_id: str
    chat_id: str

class BoolResult(BaseModel):
    result: bool

class StringResult(BaseModel):
    result: str

class CreateNewChat(BaseModel):
    user_id: str
    chat_id: str
    title: str

class ChatHistory(BaseModel):
    chat_history: List[dict] | None

class ChatIDsRequest(BaseModel):
    user_id: str

class ChatIDsResponse(BaseModel):
    chat_ids: List[str] | None

class ChatsMetadataResponse(BaseModel):
    chats_metadata: List[dict] | None

class ChatMessageTemplate(BaseModel):
    user_id: str
    chat_id: str
    sender: Literal["Human", "AI", "Tool", "Other"]
    content: str
    reasoning: Optional[List[Any]] = None
    sources: Optional[List[Any]] = None
    tools: Optional[List[Any]] = None
    additional_data: Optional[dict] = None