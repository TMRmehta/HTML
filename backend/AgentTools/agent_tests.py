import os
import json
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv

# Import your custom tools
from PLOS import PLOSSearchTool, PLOSPDFDownload
from Reddit import RedditSearch
from Summarizer import summarize_pdf

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model='gemini-1.5-flash',
    temperature=0.3,
    api_key=os.getenv('GOOGLE_API_KEY'),
    max_tokens=2048
)

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_query: str
    search_results: Dict[str, Any]
    tool_calls_history: List[Dict[str, Any]]
    reasoning_steps: List[str]
    sources_used: List[Dict[str, str]]
    final_answer: Optional[str]

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

Remember: You're helping vulnerable people understand difficult information. Be accurate, honest, and kind."""

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
    """Decide which tools to call based on reasoning"""
    
    tool_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("human", """Based on your reasoning: {reasoning}
        
        Current search results so far: {search_results}
        
        Decide which tools to call next. Remember:
        - You can call the same tool multiple times with different keywords
        - Start with broad searches, then narrow down if needed
        - Use PLOS for scientific evidence, Reddit for patient experiences
        - Download and summarize PDFs only for highly relevant papers
        
        Call the appropriate tools now.""")
    ])
    
    chain = tool_prompt | llm_with_tools
    
    response = chain.invoke({
        "messages": state['messages'],
        "reasoning": state.get('reasoning_steps', []),
        "search_results": json.dumps(state.get('search_results', {}), indent=2)
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
        "tool_calls_history": tool_calls_history
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
    """Decide whether to continue searching or provide final answer"""
    
    # Check if we have enough information
    search_results = state.get('search_results', {})
    tool_calls = state.get('tool_calls_history', [])
    
    # If we've made at least 2 tool calls and have some results, check if we need more
    if len(tool_calls) >= 2 and search_results:
        # Ask LLM if we have enough information
        check_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are evaluating if you have enough information to answer a query."),
            ("human", """Query: {query}
            
Current search results: {results}

Do you have enough relevant information to provide a comprehensive answer? 
Reply with ONLY 'continue' if you need more searches, or 'synthesize' if you have enough.""")
        ])
        
        chain = check_prompt | llm
        response = chain.invoke({
            "query": state['current_query'],
            "results": json.dumps(search_results, indent=2)[:2000]  # Truncate for context
        })
        
        if 'synthesize' in response.content.lower():
            return 'synthesize'
    
    # If we've made too many calls (>5), synthesize what we have
    if len(tool_calls) > 5:
        return 'synthesize'
    
    return 'continue'

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
class CancerResearchAssistant:
    """Main interface for the Cancer Research Assistant"""
    
    def __init__(self):
        self.agent = create_cancer_research_agent()
        self.conversation_history = []
    
    def query(self, question: str) -> Dict[str, Any]:
        """Process a user query and return the response with sources"""
        
        # Add user message to history
        user_message = HumanMessage(content=question)
        self.conversation_history.append(user_message)
        
        # Initialize state
        initial_state = {
            "messages": self.conversation_history[-10:],  # Keep last 10 messages for context
            "current_query": question,
            "search_results": {},
            "tool_calls_history": [],
            "reasoning_steps": [],
            "sources_used": [],
            "final_answer": None
        }
        
        # Run the agent
        try:
            index = 1
            for chunk in self.agent.stream(initial_state):
                print(f'Chunk {index}', '-'*100)
                print(chunk)
                index += 1
                
            # self.agent.stream()
            
            # Add assistant response to history
            # if result.get('final_answer'):
            #     self.conversation_history.append(
            #         AIMessage(content=result['final_answer'])
            #     )
            
            # return {
            #     "answer": result.get('final_answer', 'I apologize, but I couldn\'t find relevant information to answer your question.'),
            #     "sources": result.get('sources_used', []),
            #     "reasoning": result.get('reasoning_steps', [])
            # }
            
        except Exception as e:
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or asking something else.",
                "sources": [],
                "reasoning": []
            }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

# Example usage
if __name__ == "__main__":
    # Initialize the assistant
    assistant = CancerResearchAssistant()
    assistant.query('What is the current research on Lung cnacer diagnosis?')
    
    # Example queries
    # test_queries = [
    #     "What are the latest treatments for lung cancer?",
    #     "What do patients say about chemotherapy side effects?",
    #     "Can you explain immunotherapy in simple terms?"
    # ]
    
    # for query in test_queries[:1]:  # Test with first query
    #     print(f"\n{'='*60}")
    #     print(f"QUERY: {query}")
    #     print('='*60)
        
    #     response = assistant.query(query)
        
    #     print("\nANSWER:")
    #     print(response['answer'])
        
    #     print("\nSOURCES USED:")
    #     for source in response['sources']:
    #         print(f"- [{source['type']}] {source['title']}")
        
    #     print("\nREASONING STEPS:")
    #     for step in response['reasoning']:
    #         print(step)