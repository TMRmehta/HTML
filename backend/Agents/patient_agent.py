import sys, os, json, logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Generator, Literal
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, ToolMessage
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from AgentTools.PLOS import PLOSPDFDownload, PLOSSearchTool
from AgentTools.Reddit import RedditSearch
from AgentTools.Summarizer import summarize_pdf, summarize_title
# from Agents.generic_agent import cancer_research_assistant as fallback_agent
from CustomTools.models import ChatMessageTemplate
from CustomTools.ChatsManager import ChatsDatabase

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0.3,
    api_key=os.getenv('GOOGLE_API_KEY'),
    max_tokens=1024*6
)

# Init Chats Database
chat_db = ChatsDatabase()

# Init Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_query: str
    search_results: Dict[str, Any]
    tool_calls_history: List[Dict[str, Any]]
    reasoning_steps: List[str]
    sources_used: List[Dict[str, str]]
    final_answer: Optional[str]
    iterations: int   # 👈 add this


# Initialize tools
plos_search = PLOSSearchTool()
plos_downloader = PLOSPDFDownload()
reddit_search = RedditSearch()

# Create tool list
tools = [plos_search, plos_downloader, reddit_search, summarize_pdf]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# System prompt for the agent
SYSTEM_PROMPT = """You are a compassionate and knowledgeable Cancer Research Assistant designed to help patients and their families understand cancer-related research and experiences.

CORE PRINCIPLES:
1. EVIDENCE-BASED: Every claim must be grounded in either PLOS research papers or Reddit community posts
2. NO HALLUCINATION: Never generate medical advice or facts not directly from sources
3. COMPASSIONATE: Communicate with empathy, understanding you're speaking to patients/families
4. ACCESSIBLE: Explain complex medical concepts in simple, understandable terms
5. TRANSPARENT: Always cite your sources and acknowledge limitations or conflicting evidence

REASONING APPROACH (ReAct/Chain of Thought):
Before answering any query, follow these steps:

1. UNDERSTAND: What is the user really asking? Break down complex questions.
2. PLAN: What information do I need? Which tools should I use?
3. SEARCH: Use tools strategically:
   - PLOS for scientific research (max 5 keywords)
   - Reddit for patient experiences (max 8 keywords)
   - Can search multiple times with different keywords if needed
4. EVALUATE: Assess the quality and relevance of found information
5. SYNTHESIZE: Combine findings, noting agreements and conflicts
6. COMMUNICATE: Present findings clearly with proper citations

TOOL USAGE GUIDELINES:
- PLOSSearch: Use for scientific papers, treatments, clinical studies
- RedditSearch: Use for patient experiences, side effects, quality of life
- PDFDownload: Use when detailed analysis of specific papers is needed
- Summarizer: Use to extract key findings from downloaded papers

IMPORTANT RULES:
- If sources conflict, explain both perspectives
- If no relevant sources found, clearly state this limitation
- Never provide medical advice - only share what research/experiences say
- Always encourage consulting healthcare providers for personal medical decisions
- Use simple analogies to explain complex medical terms

Remember: You're helping vulnerable people understand difficult information. Be accurate, honest, compassionate and kind."""

# Node functions
def reasoning_node(state: AgentState) -> AgentState:
    """Initial reasoning about the query"""
    current_query = state['messages'][-1].content if state['messages'] else ""
    
    reasoning_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("human", """Based on the current query: '{query}'
        
        Think step by step:
        1. What specific information is the user seeking?
        2. What sources would be most appropriate (research papers vs patient experiences)?
        3. What keywords would be most effective for searching (remember: max 5 for PLOS, max 8 for Reddit)?
        4. Should I search multiple times with different keywords?
        
        Provide your reasoning and initial search plan.""")
    ])
    
    chain = reasoning_prompt | llm
    response = chain.invoke({
        "messages": state['messages'],
        "query": current_query
    })
    
    reasoning_steps = [response.content]
    
    return {
        **state,
        "current_query": current_query,
        "reasoning_steps": reasoning_steps
    }


def tool_calling_node(state: AgentState) -> AgentState:
    """Decide which tool to call (one at a time for Gemini)"""
    
    # Check how many tool calls we've already made
    tool_calls_count = len(state.get('tool_calls_history', []))
    
    tool_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT + """
        IMPORTANT: You can only call ONE tool at a time. Choose the most important tool call for this step.
        If you need multiple searches, you'll get another chance in the next iteration."""),
        MessagesPlaceholder(variable_name="messages"),
        ("human", """Based on your reasoning: {reasoning}
        
        Current search results so far: {search_results}
        Tool calls made so far: {tool_calls_count}
                
        Choose ONE tool to call next. Priority:
        1. If no research found yet: Use PLOS search first
        2. If research exists but no patient experiences: Use Reddit search  
        3. If you have both but need specific paper details: Use PDF download
        4. If you have content to summarize: Use summarizer

        Call only ONE tool now.""")
            ])
    
    chain = tool_prompt | llm_with_tools
    
    response = chain.invoke({
        "messages": state['messages'],
        "reasoning": state.get('reasoning_steps', []),
        "search_results": json.dumps(state.get('search_results', {}), indent=2),
        "tool_calls_count": tool_calls_count
    })
    
    # Update messages with tool calls
    messages = state['messages'] + [response]
    
    return {
        **state,
        "messages": messages
    }


def process_tools_node(state: AgentState) -> AgentState:
    """Process the results from tool calls"""
    
    # Get the last message which should contain tool calls
    last_message = state['messages'][-1]
    
    # Execute tools and collect results
    tool_node = ToolNode(tools)
    result = tool_node.invoke(state)
    
    # Extract and store tool results
    search_results = state.get('search_results', {})
    tool_calls_history = state.get('tool_calls_history', [])
    
    # Parse tool results and update search_results
    for message in result['messages']:
        if hasattr(message, 'content'):
            try:
                # Store the raw results
                timestamp = datetime.now().isoformat()
                search_results[timestamp] = message.content
                tool_calls_history.append({
                    'timestamp': timestamp,
                    'result': message.content
                })
            except:
                pass
    
    return {
        **state,
        "messages": result['messages'],
        "search_results": search_results,
        "tool_calls_history": tool_calls_history,
        "iterations": state.get("iterations", 0) + 1  # 👈 increment
    }


def synthesis_node(state: AgentState) -> AgentState:
    """Synthesize all findings into a coherent answer"""
    
    synthesis_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("human", """You have gathered the following information:

Search Results:
{search_results}

Now synthesize this information to answer the original query: '{query}'

Guidelines for your response:
1. Start with a brief, empathetic acknowledgment of the question
2. Present findings organized by source type (Research papers vs Patient experiences)
3. Use simple language and explain medical terms with analogies
4. Clearly cite each source (paper title or Reddit post)
5. If there are conflicting findings, explain both perspectives
6. End with important caveats or encouragement to consult healthcare providers
7. If insufficient information was found, be honest about limitations

Format your response with clear sections:
- Summary of Findings
- Research Evidence (from PLOS)
- Patient Experiences (from Reddit)
- Important Considerations
- Sources Used

Remember: Be accurate, compassionate, and never generate information not found in sources.""")
    ])
    
    chain = synthesis_prompt | llm
    
    response = chain.invoke({
        "messages": state['messages'],
        "search_results": json.dumps(state.get('search_results', {}), indent=2),
        "query": state['current_query']
    })
    
    # Extract sources from search results
    sources_used = []
    search_results = state.get('search_results', {})
    
    for timestamp, result in search_results.items():
        if isinstance(result, str):
            try:
                result_data = json.loads(result) if isinstance(result, str) else result
                
                # Extract PLOS sources
                if 'articles' in result_data:
                    for article in result_data['articles']:
                        sources_used.append({
                            'type': 'PLOS Research',
                            'title': article.get('title', 'Unknown'),
                            'id': article.get('id', '')
                        })
                
                # Extract Reddit sources
                elif isinstance(result_data, list) and len(result_data) > 0:
                    if 'subreddit' in result_data[0]:
                        for post in result_data[:3]:  # Limit to top 3 Reddit posts
                            sources_used.append({
                                'type': 'Reddit Post',
                                'title': post.get('title', 'Unknown'),
                                'subreddit': post.get('subreddit', '')
                            })
            except:
                continue
    
    return {
        **state,
        "messages": state['messages'] + [AIMessage(content=response.content)],
        "final_answer": response.content,
        "sources_used": sources_used
    }

def should_continue(state: AgentState) -> str:
    # Hard stop after N iterations
    if state.get("iterations", 0) >= 5:   # 👈 change N as needed
        return "synthesize"

    search_results = state.get('search_results', {})
    tool_calls = state.get('tool_calls_history', [])

    if len(tool_calls) >= 2 and search_results:
        check_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are evaluating if you have enough information to answer a query."),
            ("human", """Query: {query}
            
            Current search results: {results}

            Do you have enough relevant information to provide a comprehensive answer? 
            Reply ONLY 'continue' or 'synthesize'.""")
        ])
        chain = check_prompt | llm
        response = chain.invoke({
            "query": state['current_query'],
            "results": json.dumps(search_results, indent=2)[:2000]
        })
        
        if 'synthesize' in response.content.lower():
            return 'synthesize'

    return "continue"


# Build the graph
def create_cancer_research_agent():
    """Create and compile the LangGraph agent"""
    
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("reason", reasoning_node)
    workflow.add_node("call_tools", tool_calling_node)
    workflow.add_node("process_tools", process_tools_node)
    workflow.add_node("synthesize", synthesis_node)
    
    # Define the flow
    workflow.set_entry_point("reason")
    
    # Add edges
    workflow.add_edge("reason", "call_tools")
    workflow.add_edge("call_tools", "process_tools")
    
    # Conditional edge from process_tools
    workflow.add_conditional_edges(
        "process_tools",
        should_continue,
        {
            "continue": "call_tools",
            "synthesize": "synthesize"
        }
    )
    
    # End after synthesis
    workflow.add_edge("synthesize", END)
    
    # Compile the graph
    app = workflow.compile()
    return app


# Main interface class
class PatientAgent():
    """Main interface for the Cancer Research Assistant"""
    
    def __init__(self, history:Optional[List] = None, debug:bool = False):
        self.agent = create_cancer_research_agent()
        self.debug = debug

        if history is None:
            self.conversation_history = []

        logger.info("✅ Init Patient Agent")


    def fetch_db_history(self, user_id:str, chat_id:str):
        formatted_history = []
        history = chat_db.fetch_chat(user_id, chat_id)
        
        if self.debug:
            print("DEBUG CHAT HISTORY {fetch_db_history} \n", history)

        if history is not None:
            for message in history:
                if message["sender"] == 'Human':
                    formatted_history.append(
                        HumanMessage(content=message["content"])
                    )

                elif message["sender"] == 'AI':
                    formatted_history.append(
                        AIMessage(content=message["content"])
                    )

                elif message["sender"] == 'Tool':
                    formatted_history.append(
                        ToolMessage(content=message["content"])
                    )

        return formatted_history
    
    
    def query(self, question:str, user_id:str, chat_id:str) -> Dict[str, Any]:
        """Process a user query and return the response with sources"""
        if not chat_db.chat_exists(user_id, chat_id):
            chat_db.create_chat(user_id, chat_id, summarize_title(question))
        
        self.conversation_history = self.fetch_db_history(user_id, chat_id)

        # Add user message to history
        user_message = HumanMessage(content=question)
        self.conversation_history.append(user_message)
        chat_db.add_question(ChatMessageTemplate(
            user_id=user_id,
            chat_id=chat_id,
            sender='Human',
            content=question
        ))

        # Initialize state
        initial_state = {
            "messages": self.conversation_history[-5:],  # Keep last 5 messages for context
            "current_query": question,
            "search_results": {},
            "tool_calls_history": [],
            "reasoning_steps": [],
            "sources_used": [],
            "final_answer": None
        }

        try:
            result = self.agent.invoke(initial_state)
            
            # Add assistant response to history
            if result.get('final_answer'):
                self.conversation_history.append(
                    AIMessage(content=result['final_answer'])
                )
            
            return chat_db.add_response(ChatMessageTemplate(
                user_id=user_id,
                chat_id=chat_id,
                sender='AI',
                content=result.get('final_answer', 'I apologize, but I couldn\'t find relevant information to answer your question.'),
                sources=result.get('sources_used', None),
                reasoning=result.get('reasoning_steps', None)
            ))
        
        # except RecursionError:
        #     logger.error("Recursion limit hit, forcing synthesis fallback.")
        #     result = synthesis_node(initial_state)  # 👈 manual fallback
            
        except Exception as e:
            logger.critical(f"Failed to generate LLM response for question {question} Exception - {e}")
            return chat_db.add_response(ChatMessageTemplate(
                user_id=user_id,
                chat_id=chat_id,
                sender='AI',
                content="I apologize, but I'm having trouble reaching my sources, so I am unable find relevant information to answer your question.",
                additional_data={
                    "status":"failed",
                    "error":e
                }
            ))
            
        
    def clear_history(self) -> bool:
        """Clear conversation history"""
        self.conversation_history = []
        return True
        
    def get_history(self) -> list:
        return self.conversation_history


# Example usage
if __name__ == "__main__":
    # Initialize the assistant
    assistant = PatientAgent(debug=True)
    from pprint import pprint
    
    test_user = "putcZPfnudmgXrMMOG0m"
    test_chat = "new_chat_22-09-2025"
    test_queries = [
        'Can you find information experiences from patients who have recovered from lung cancer?'
    ]
    
    for query in test_queries[:1]:  # Test with first query
        print(f"QUERY: {query}")
        print()
        
        response = assistant.query(question=query, user_id=test_user, chat_id=test_chat)
        pprint(response)