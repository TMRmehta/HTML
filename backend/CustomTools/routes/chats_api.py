from CustomTools.models import (
    ChatLookup,
    BoolResult,
    StringResult,
    ChatHistory,
    ChatIDsRequest,
    ChatIDsResponse,
    ChatsMetadataResponse
)
from CustomTools.ChatsManager import ChatsDatabase
from AgentTools.Summarizer import summarize_title
import sys
import os
import logging
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# from Agents.models import (
#     ChatAPIRequest,
#     ChatRequest,
#     ChatResponse,
#     PatientChatResponse,
#     ChatAPIAnswer
# )


chatdb = ChatsDatabase()
# app = FastAPI()
router = APIRouter(prefix="/chats", tags=["chats", "chat_history", "chats_db"])


@router.get("/")
async def root():
    return "Chats Database API Active"


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Oncosight Chats Database is working"}


@router.post("/exists", response_model=BoolResult)
async def chat_exists_check(request: ChatLookup):
    """Check if a chat_id exists in the database for a given user_id"""
    return BoolResult(result=chatdb.chat_exists(request.user_id, request.chat_id))
    return BoolResult(result=chatdb.chat_exists(request.user_id, request.chat_id))


@router.post("/fetch_history", response_model=ChatHistory)
async def fetch_chat_histoy(request: ChatLookup):
    """Fetch full chat history for a given chat_id from the database"""
    fetched_history = chatdb.fetch_chat(request.user_id, request.chat_id)
    return ChatHistory(chat_history=fetched_history)


@router.post("/get_ids", response_model=ChatIDsResponse)
async def get_chat_ids_list(request: ChatIDsRequest):
    """Fetch chat_ids only for a given user_id"""
    found_ids = chatdb.get_chat_ids(request.user_id)
    return ChatIDsResponse(chat_ids=found_ids)


@router.post("/get_metadata", response_model=ChatsMetadataResponse)
async def get_chats_with_metadata(request: ChatIDsRequest):
    """Fetch chat_ids with metdatar only for a given user_id"""
    found_chats = chatdb.get_chats_metadata(request.user_id)
    return ChatsMetadataResponse(chats_metadata=found_chats)


@router.post("/get_title", response_model=StringResult)
async def chat_id(request: ChatLookup):
    title = chatdb.fetch_chat_title(request.user_id, request.chat_id)
    return StringResult(result=title)


@router.post("/user_exists", response_model=BoolResult)
async def user_existance_check(request: ChatIDsRequest):
    return BoolResult(result=chatdb.user_exists(request.user_id))


@router.post("/create_chat_user", response_model=BoolResult)
async def create_new_chat_user(request: ChatIDsRequest):
    return BoolResult(result=chatdb.create_new_user(request.user_id))


# @router.post("/create_chat", response_model=BoolResult)
# async def create_chat(requst:CreateNewChat):
#     """Create a new chat with a title that summarizes the first question"""
#     new_title = summarize_title(CreateNewChat.title)
#     status = chatdb.create_chat(requst.user_id, requst.chat_id, new_title)
#     return BoolResult(status)


# @router.post("/save_question", response_model=BoolResult)
# async def save_question(request:ChatMessageTemplate):
#     """Add a question to chat database and autmatically generate a title"""
#     if not chatdb.chat_exists(request.user_id, request.chat_id):
#         created = chatdb.create_chat(
#                             user_id=request.user_id,
#                             chat_id=request.chat_id,
#                             title=summarize_title(request.content)
#                         )

#     if created:
#         status = chatdb.add_question(request.user_id, request.chat_id, request.content)

#         if status is not None:
#             return BoolResult(True)

#     logging.critical(f'Failed to add question "{request.question}" for user_id {request.user_id} chat_id {request.chat_id}')
#     return BoolResult(False)


# @router.post("/save_answer", response_model=BoolResult)
# async def save_answer(request:ChatMessageTemplate):
#     send_data = ChatResponse(
#         answer=request.answer,
#         reasoning=request.reasoning,
#         sources=request.sources,
#         tools=request.tools,
#         type=request.type
#     )

#     if chatdb.chat_exists(request.user_id, request.chat_id):
#         save_status = chatdb.add_response(
#             user_id=request.user_id,
#             chat_id=request.chat_id,
#             data=send_data
#         )
