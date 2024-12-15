import PyPDF2
import praw
import arxiv

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, asdict

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import AgentExecutor, create_react_agent, initialize_agent, AgentType
from langchain.prompts import PromptTemplate

from langchain import hub

from langchain.tools import BaseTool, tool
from langchain_community.tools import DuckDuckGoSearchRun

from langchain.schema import BaseMessage, SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI

from langchain_community.tools.tavily_search import TavilySearchResults