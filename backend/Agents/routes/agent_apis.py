from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from uuid import UUID

import os, sys, logging, traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from CustomTools.ChatsManager import ChatsDatabase
from CustomTools.models import ChatMessageTemplate
from Agents.models import ChatRequest, ChatResponse, ChatAPIRequest, PatientChatResponse, ResearchChatResponse
from Agents.generic_agent import cancer_research_assistant
from Agents.patient_agent import PatientAgent
from Agents.research_agent import ResearchAgent



router = APIRouter(prefix="/agents", tags=["agents"])
# app = FastAPI()
patient_agent = PatientAgent()
research_agent = ResearchAgent()
ChatDB = ChatsDatabase()

@router.get("/")
async def root():
    return "Agent API Active"


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Oncosight.AI API is running"}


@router.post("/generic", response_model=ChatResponse)
async def general_chat(request: ChatAPIRequest):
    """Chat with fallback LLM, in case main agent fails"""

    try:
        logger.debug(f"Submitted Question {request.question} for User {request.user_id}")
        answer = ChatResponse(answer=cancer_research_assistant(request.question))

        _ = ChatDB.add_question(ChatMessageTemplate(
            user_id=request.user_id,
            chat_id=request.chat_id,
            sender="Human",
            content=request.question,
            additional_data={
                "agent_type":"fallback_patient"
            }
        ))

        _ = ChatDB.add_response(ChatMessageTemplate(
            user_id=request.user_id,
            chat_id=request.chat_id,
            sender="AI",
            content=answer,
            additional_data={
                "agent_type":"fallback_patient"
            }
        ))

        return PatientChatResponse(
            answer=answer,
            return_status="fallback"
        )

    except Exception as e:
        return PatientChatResponse(
            answer="An error occoured while generating your answer",
            return_status="failed"
        )


@router.post("/patient", response_model=PatientChatResponse)
async def patient_chat(request: ChatAPIRequest):
    """Chat with Patient Agent"""

    try:
        logger.debug(f"Submitted Question {request.question} for User {request.user_id}")
        result = patient_agent.query(user_id=request.user_id, chat_id=request.chat_id, question=request.question)
        return PatientChatResponse(
            answer=result["content"],
            reasoning=result["reasoning"],
            sources=result["sources"],
            return_status="success"
        )

    except KeyboardInterrupt:
        exit()

    except Exception as e:
        logger.critical(f"Failed to fetch answer for question {request.question} Exception - {traceback.format_exc()}")
        return PatientChatResponse(
            answer="An error occoured while generating your answer",
            return_status="failed"
        )
    

@router.post("/research", response_model=ResearchChatResponse)
async def patient_chat(request: ChatAPIRequest):
    """Chat with Research Agent"""

    try:
        logger.debug(f"Submitted Question {request.question} for User {request.user_id}")
        result = research_agent.query(user_id=request.user_id, chat_id=request.chat_id, question=request.question)
        return ResearchChatResponse(
            answer=result["content"],
            reasoning=result["reasoning"],
            sources=result["sources"],
            return_status="success"
        )

    except KeyboardInterrupt:
        exit()

    except Exception as e:
        logger.critical(f"Failed to fetch answer for question {request.question} Exception - {traceback.format_exc()}")
        return ResearchChatResponse(
            answer="An error occoured while generating your answer",
            return_status="failed"
        )



# @router.post("/stream", response_model=PatientChatResponse)
# async def stream_question(request:ChatAPIRequest):
#     """Streaming response chat with Patient Agent"""
#     return StreamingResponse(
#         content=agent.query(request.question, mode='stream'),
#         media_type="application/json"
#     )


if __name__ == "__main__":
    test_user = "putcZPfnudmgXrMMOG0m"
    test_chat = "new_chat_22-09-2025"