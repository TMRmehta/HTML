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
from CustomTools.models import ChatMessageTemplate
from CustomTools.ChatsManager import ChatsDatabase

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0.2,  # Lower temperature for more precise technical responses
    api_key=os.getenv('GOOGLE_API_KEY'),
    max_tokens=1024*8  # Increased for verbose responses
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
    iterations: int
    technical_focus: List[str]
    simple_search_terms: List[str]  # Track simple terms for PLOS
    data_availability: str  # Track whether we have external data

# Initialize tools
plos_search = PLOSSearchTool()
plos_downloader = PLOSPDFDownload()
reddit_search = RedditSearch()

# Create tool list
tools = [plos_search, plos_downloader, reddit_search, summarize_pdf]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# System prompt for the cancer research agent
SYSTEM_PROMPT = """You are an advanced Cancer Research Analyst AI designed to provide comprehensive, technical, and highly detailed analysis of cancer-related research and clinical data.

CORE MISSION:
Deliver exhaustive, scientifically rigorous analysis of cancer research with maximum technical depth and precision.

RESPONSE CHARACTERISTICS:
1. HIGHLY VERBOSE: Provide extensive detail, comprehensive explanations, and thorough analysis
2. TECHNICAL DEPTH: Use precise scientific terminology, molecular mechanisms, pathway analysis
3. QUANTITATIVE FOCUS: Include statistical data, effect sizes, confidence intervals, p-values when available
4. MECHANISTIC UNDERSTANDING: Explain biological pathways, molecular interactions, cellular processes
5. CLINICAL CORRELATION: Connect basic research to clinical implications and therapeutic potential

ANALYTICAL FRAMEWORK:
1. MOLECULAR LEVEL: Analyze genetic mutations, protein interactions, signaling cascades
2. CELLULAR LEVEL: Examine cell cycle disruption, apoptosis mechanisms, metabolic alterations
3. TISSUE LEVEL: Evaluate tumor microenvironment, angiogenesis, metastatic processes
4. SYSTEMIC LEVEL: Consider immune responses, drug metabolism, biomarker expression
5. CLINICAL LEVEL: Assess therapeutic efficacy, resistance mechanisms, prognostic factors

REASONING METHODOLOGY (Enhanced ReAct):
1. COMPREHENSIVE ANALYSIS: Break down complex queries into multiple technical sub-questions
2. STRATEGIC SEARCH: Design targeted searches for:
   - Mechanistic studies (PLOS: molecular pathways, drug targets)
   - Clinical trials (PLOS: efficacy data, biomarkers, outcomes)
   - Real-world experiences (Reddit: treatment responses, side effect profiles)
3. MULTI-DIMENSIONAL EVALUATION: Assess findings across:
   - Study design quality (RCT vs observational)
   - Sample sizes and statistical power
   - Mechanistic plausibility
   - Clinical relevance and applicability
4. SYNTHESIS: Integrate findings into comprehensive technical analysis
5. CRITICAL ASSESSMENT: Identify knowledge gaps, conflicting evidence, research limitations

TECHNICAL COMMUNICATION STANDARDS:
- Use precise oncological terminology (e.g., "tumor suppressor gene inactivation" not "cancer gene problems")
- Include molecular details (e.g., "PI3K/AKT/mTOR pathway dysregulation")
- Specify cancer subtypes and staging when relevant
- Discuss biomarkers, genetic profiles, and molecular classifications
- Address drug mechanisms of action at molecular level
- Include pharmacokinetic and pharmacodynamic considerations

TOOL UTILIZATION STRATEGY:
- PLOSSearch: Target high-impact research, clinical trials, mechanistic studies
- RedditSearch: Capture real-world treatment experiences, adverse events, quality of life data
- PDFDownload: Extract detailed methodology, statistical analyses, supplementary data
- Summarizer: Distill complex findings while maintaining technical accuracy

RESPONSE STRUCTURE:
1. Executive Summary (technical overview)
2. Mechanistic Analysis (molecular/cellular level detail)
3. Clinical Evidence Review (trial data, outcomes, statistics)
4. Real-World Evidence (patient experiences, practical considerations)
5. Critical Analysis (limitations, conflicting data, research gaps)
6. Future Directions (emerging therapies, ongoing trials)
7. Technical Appendix (detailed citations, methodology notes)

QUALITY STANDARDS:
- Every claim must be source-attributed with specific study details
- Include study limitations and potential biases
- Distinguish between correlation and causation
- Address statistical significance vs clinical significance
- Acknowledge uncertainty and conflicting evidence
- Provide context for generalizability

Remember: You are addressing fellow researchers, clinicians, and advanced students who expect maximum technical depth and scientific rigor.

IMPORTANT NOTE - If user submits a generic question/greeting like "Hi", "Hello", "thanks" etc, please do not invoke any tools, just answer it directly and prompt the user to ask a research related question.
"""

# Node functions
def reasoning_node(state: AgentState) -> AgentState:
    """Enhanced reasoning for technical cancer research queries with simplified search strategy"""
    current_query = state['messages'][-1].content if state['messages'] else ""
    
    reasoning_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("human", """Analyze this cancer research query: '{query}'

        Design a SIMPLE but effective search strategy:
        1. CANCER TYPE: Identify main cancer type (lung, breast, colon, etc.)
        2. KEY CONCEPT: What's the main research focus? (treatment, mechanism, biomarker, etc.)
        3. SIMPLE SEARCH TERMS: 
           - PLOS: Use ONLY 1-3 simple words (e.g., "lung cancer", "EGFR", "immunotherapy")
           - Reddit: Use 4-6 practical terms patients would use
        4. FALLBACK PLAN: If no results, what alternative searches or knowledge to use?
        
        IMPORTANT: Keep PLOS searches extremely simple - the API has limitations.
        Examples of GOOD PLOS searches: "lung cancer", "breast cancer treatment", "EGFR inhibitor"
        Examples of BAD PLOS searches: "molecular mechanisms underlying resistance", "tyrosine kinase inhibitor mechanisms"
        
        Provide your analysis and SIMPLE search strategy.""")
    ])
    
    chain = reasoning_prompt | llm
    response = chain.invoke({
        "messages": state['messages'],
        "query": current_query
    })
    
    reasoning_steps = [response.content]
    
    # Extract technical focus areas and simplified search terms
    technical_focus = []
    simple_search_terms = []
    content_lower = response.content.lower()
    
    focus_areas = [
        "molecular mechanisms", "signaling pathways", "biomarkers", "clinical trials",
        "therapeutic targets", "drug resistance", "metastasis", "tumor microenvironment",
        "immunotherapy", "precision medicine", "genetic mutations", "epigenetics"
    ]
    
    for area in focus_areas:
        if area in content_lower:
            technical_focus.append(area)
    
    # Extract cancer types for simple searches
    cancer_types = ["lung cancer", "breast cancer", "colon cancer", "prostate cancer", 
                   "melanoma", "leukemia", "lymphoma", "pancreatic cancer"]
    
    for cancer_type in cancer_types:
        if cancer_type.replace(" cancer", "") in content_lower:
            simple_search_terms.append(cancer_type)
            break
    
    return {
        **state,
        "current_query": current_query,
        "reasoning_steps": reasoning_steps,
        "technical_focus": technical_focus,
        "simple_search_terms": simple_search_terms
    }

def tool_calling_node(state: AgentState) -> AgentState:
    """Strategic tool selection with simplified PLOS searches"""
    
    tool_calls_count = len(state.get('tool_calls_history', []))
    
    tool_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT + """
        
        CRITICAL PLOS API CONSTRAINTS:
        - Use ONLY 1-3 simple words for PLOS searches
        - Avoid complex technical phrases
        - Focus on basic terms like: "lung cancer", "chemotherapy", "EGFR", "immunotherapy"
        - If previous PLOS searches failed, try even simpler terms or skip to Reddit/summarization
        
        TOOL SELECTION PRIORITY:
        1. Simple PLOS Search: Basic cancer terms only
        2. Reddit Search: Patient experiences (more flexible with keywords)
        3. PDF Download: Only if PLOS returned specific papers
        4. Summarizer: If have PDF content to analyze
        
        FALLBACK STRATEGY:
        - If PLOS consistently fails, focus on Reddit and existing knowledge
        - Use your training knowledge as primary source with caveats about limitations"""),
        MessagesPlaceholder(variable_name="messages"),
        ("human", """Current situation: {search_results}
        Tool calls made: {tool_calls_count}
        Simple search terms identified: {simple_terms}
        
        PLOS API STATUS: Check if previous PLOS searches returned actual data or empty results.
        
        If PLOS searches are failing:
        - Try ONE more time with the simplest possible terms (1-2 words)
        - OR switch to Reddit search for patient experiences
        - OR acknowledge limitations and synthesize from available knowledge
        
        Choose ONE tool strategically, keeping PLOS limitations in mind.""")
    ])
    
    chain = tool_prompt | llm_with_tools
    
    response = chain.invoke({
        "messages": state['messages'],
        "search_results": json.dumps(state.get('search_results', {}), indent=2),
        "tool_calls_count": tool_calls_count,
        "simple_terms": ', '.join(state.get('simple_search_terms', []))
    })
    
    messages = state['messages'] + [response]
    
    return {
        **state,
        "messages": messages
    }

def process_tools_node(state: AgentState) -> AgentState:
    """Process and categorize tool results for technical analysis"""
    
    last_message = state['messages'][-1]
    
    tool_node = ToolNode(tools)
    result = tool_node.invoke(state)
    
    search_results = state.get('search_results', {})
    tool_calls_history = state.get('tool_calls_history', [])
    
    # Enhanced result processing for technical content
    for message in result['messages']:
        if hasattr(message, 'content'):
            try:
                timestamp = datetime.now().isoformat()
                
                # Categorize results for better technical analysis
                result_category = "general"
                content = str(message.content).lower()
                
                if "clinical trial" in content or "randomized" in content:
                    result_category = "clinical_evidence"
                elif "mechanism" in content or "pathway" in content or "molecular" in content:
                    result_category = "mechanistic_research"
                elif "patient" in content or "treatment experience" in content:
                    result_category = "patient_evidence"
                elif "biomarker" in content or "genetic" in content:
                    result_category = "biomarker_research"
                
                search_results[f"{result_category}_{timestamp}"] = message.content
                tool_calls_history.append({
                    'timestamp': timestamp,
                    'result': message.content,
                    'category': result_category
                })
            except Exception as e:
                logger.warning(f"Error processing tool result: {e}")
    
    return {
        **state,
        "messages": result['messages'],
        "search_results": search_results,
        "tool_calls_history": tool_calls_history,
        "iterations": state.get("iterations", 0) + 1
    }

def synthesis_node(state: AgentState) -> AgentState:
    """Comprehensive technical synthesis with fallback to foundational knowledge"""
    
    # Check if we have any meaningful search results
    search_results = state.get('search_results', {})
    has_external_data = False
    
    for key, result in search_results.items():
        if result and isinstance(result, str):
            try:
                result_data = json.loads(result) if result.startswith('{') or result.startswith('[') else result
                if (isinstance(result_data, dict) and result_data.get('articles')) or \
                   (isinstance(result_data, list) and len(result_data) > 0):
                    has_external_data = True
                    break
            except:
                if len(str(result).strip()) > 50:  # Some meaningful content
                    has_external_data = True
                    break
    
    if has_external_data:
        # Standard synthesis with external data
        synthesis_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
            ("human", """Synthesize comprehensive technical analysis from gathered research:

Research Data:
{search_results}

Original Query: '{query}'
Technical Focus Areas: {technical_focus}

Create an exhaustive, highly technical response with the following structure:

## EXECUTIVE SUMMARY
- Provide concise but comprehensive overview of key findings
- Highlight most significant research insights and clinical implications

## MECHANISTIC ANALYSIS
- Detail molecular mechanisms, signaling pathways, and biological processes
- Include specific protein interactions, genetic alterations, and cellular effects
- Use precise oncological terminology and molecular detail

## CLINICAL EVIDENCE REVIEW
- Analyze available data with statistical details where possible
- Include study methodologies, patient populations, and outcome measures
- Discuss therapeutic efficacy, safety profiles, and clinical significance

## REAL-WORLD EVIDENCE
- Integrate patient experiences and practical treatment considerations
- Address quality of life impacts and real-world effectiveness

## CRITICAL ANALYSIS
- Identify study limitations and areas of uncertainty
- Address gaps in current knowledge based on available data

## THERAPEUTIC IMPLICATIONS
- Discuss treatment approaches based on available evidence
- Address personalized medicine opportunities where supported

## SOURCES AND LIMITATIONS
- Provide detailed source attributions
- Clearly acknowledge any limitations in the available data
- Distinguish between established facts and areas requiring further research

Generate comprehensive technical analysis using ALL available sources.""")
        ])
    else:
        # Fallback synthesis using foundational knowledge
        synthesis_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT + """
            
            IMPORTANT: External data sources were not accessible or returned limited results. 
            Base your analysis on established scientific consensus and foundational oncology knowledge, 
            while clearly acknowledging these limitations."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", """FALLBACK ANALYSIS MODE - Limited External Data Available

Original Query: '{query}'
Technical Focus Areas: {technical_focus}
Search Attempts: {search_results}

Since external research databases provided limited results, synthesize from established oncology knowledge:

## METHODOLOGICAL NOTE
- Clearly state that external database searches were unsuccessful
- Note reliance on established scientific consensus
- Acknowledge limitations of this approach

## COMPREHENSIVE ANALYSIS FROM ESTABLISHED KNOWLEDGE
Based on foundational oncology research and established scientific consensus:

### Molecular and Cellular Mechanisms
- Detail known pathways and mechanisms from established literature
- Include key protein interactions and signaling cascades
- Reference well-established molecular biology principles

### Clinical Context
- Discuss standard treatment approaches
- Include known biomarkers and therapeutic targets
- Address established clinical outcomes and prognostic factors

### Current Research Landscape
- Outline major research directions in this area
- Discuss established clinical trials and their outcomes
- Address known challenges and limitations

### Future Directions
- Suggest areas where research is typically focused
- Discuss emerging approaches based on established trends

## CRITICAL LIMITATIONS
- Explicitly acknowledge lack of current external data
- Note that information is based on general oncology knowledge
- Recommend consulting current literature for latest developments
- Suggest specific databases or resources for current information

## RECOMMENDATIONS
- Advise verification with current peer-reviewed sources
- Suggest consulting with oncology specialists
- Recommend accessing institutional research databases

Generate detailed analysis while being completely transparent about data limitations.""")
        ])
    
    chain = synthesis_prompt | llm
    
    response = chain.invoke({
        "messages": state['messages'],
        "search_results": json.dumps(search_results, indent=2) if has_external_data else "Limited external data retrieved",
        "query": state['current_query'],
        "technical_focus": ', '.join(state.get('technical_focus', []))
    })
    
    # Enhanced source extraction
    sources_used = []
    
    if has_external_data:
        for key, result in search_results.items():
            if isinstance(result, str):
                try:
                    result_data = json.loads(result) if result.startswith('{') or result.startswith('[') else {"content": result}
                    
                    # Extract PLOS sources
                    if 'articles' in result_data:
                        for article in result_data['articles'][:3]:  # Limit to top 3
                            sources_used.append({
                                'type': 'PLOS Research Paper',
                                'title': article.get('title', 'Unknown'),
                                'id': article.get('id', ''),
                                'category': key.split('_')[0] if '_' in key else 'research'
                            })
                    
                    # Extract Reddit sources
                    elif isinstance(result_data, list) and len(result_data) > 0:
                        if 'subreddit' in str(result_data[0]):
                            for post in result_data[:3]:
                                sources_used.append({
                                    'type': 'Reddit Patient Experience',
                                    'title': post.get('title', 'Patient Report')[:100] + '...' if len(post.get('title', '')) > 100 else post.get('title', 'Patient Report'),
                                    'subreddit': post.get('subreddit', ''),
                                    'category': 'patient_evidence'
                                })
                except Exception as e:
                    logger.warning(f"Error extracting sources: {e}")
                    continue
    else:
        sources_used.append({
            'type': 'Foundational Knowledge',
            'title': 'Established oncology research consensus',
            'note': 'External databases were not accessible - analysis based on training knowledge',
            'limitation': 'Current research may not be reflected'
        })
    
    return {
        **state,
        "messages": state['messages'] + [AIMessage(content=response.content)],
        "final_answer": response.content,
        "sources_used": sources_used,
        "data_availability": "external_data" if has_external_data else "foundational_knowledge"
    }

def should_continue(state: AgentState) -> str:
    """Enhanced continuation logic for comprehensive research"""
    
    # Hard stop after more iterations for thorough research
    if state.get("iterations", 0) >= 6:
        return "synthesize"
    
    search_results = state.get('search_results', {})
    tool_calls = state.get('tool_calls_history', [])
    
    # Check if we have sufficient research across different categories
    if len(tool_calls) >= 3 and search_results:
        check_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are evaluating research completeness for technical cancer research analysis.
            Consider whether sufficient evidence exists across:
            - Primary research/clinical trials
            - Mechanistic studies
            - Patient experiences
            - Detailed paper analysis"""),
            ("human", """Query: {query}
            Technical focus: {technical_focus}
            Current research: {results}
            
            Do you have sufficient comprehensive research for detailed technical analysis?
            Consider research depth, breadth, and technical detail available.
            
            Reply ONLY 'continue' or 'synthesize'.""")
        ])
        
        chain = check_prompt | llm
        response = chain.invoke({
            "query": state['current_query'],
            "technical_focus": ', '.join(state.get('technical_focus', [])),
            "results": json.dumps(search_results, indent=2)[:3000]
        })
        
        if 'synthesize' in response.content.lower():
            return 'synthesize'
    
    return "continue"

# Build the graph
def create_cancer_research_agent():
    """Create and compile the enhanced cancer research LangGraph agent"""
    
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
class ResearchAgent:
    """Advanced Cancer Research Analysis Agent"""
    
    def __init__(self, history: Optional[List] = None, debug: bool = False):
        self.agent = create_cancer_research_agent()
        self.debug = debug
        if history is None:
            self.conversation_history = []
        logger.info("✅ Initialized Cancer Research Agent")
    
    def fetch_db_history(self, user_id: str, chat_id: str):
        """Fetch conversation history from database"""
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
    
    def query(self, question: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """Process cancer research query with robust error handling and fallback strategies"""
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
        
        # Initialize state with enhanced structure
        initial_state = {
            "messages": self.conversation_history[-5:],
            "current_query": question,
            "search_results": {},
            "tool_calls_history": [],
            "reasoning_steps": [],
            "sources_used": [],
            "final_answer": None,
            "iterations": 0,
            "technical_focus": [],
            "simple_search_terms": []
        }
        
        try:
            result = self.agent.invoke(initial_state)
            
            # Determine response quality based on data availability
            data_availability = result.get('data_availability', 'unknown')
            final_answer = result.get('final_answer')
            
            # Add assistant response to history
            if final_answer:
                self.conversation_history.append(
                    AIMessage(content=final_answer)
                )
            
            # Prepare response with appropriate messaging based on data availability
            if data_availability == 'foundational_knowledge':
                content_prefix = "**Note: External research databases were not fully accessible. This analysis is based on established oncology knowledge and may not reflect the most recent research developments.**\n\n"
                final_answer = content_prefix + (final_answer or "Unable to provide comprehensive analysis due to data access limitations.")
            
            return chat_db.add_response(ChatMessageTemplate(
                user_id=user_id,
                chat_id=chat_id,
                sender='AI',
                content=final_answer or 'I apologize, but I encountered difficulties accessing research databases and cannot provide the comprehensive technical analysis requested.',
                sources=result.get('sources_used', None),
                reasoning=result.get('reasoning_steps', None),
                additional_data={
                    "technical_focus": result.get('technical_focus', []),
                    "research_depth": len(result.get('tool_calls_history', [])),
                    "iterations": result.get('iterations', 0),
                    "data_availability": data_availability,
                    "search_attempts": len(result.get('search_results', {})),
                    "api_status": "limited" if data_availability == 'foundational_knowledge' else "functional"
                }
            ))
        
        except Exception as e:
            logger.critical(f"Failed to generate research analysis for question: {question}. Exception: {e}")
            
            # Provide a more helpful error message with suggestions
            error_response = f"""I apologize, but I encountered a technical error while processing your cancer research query.

**Error Details:** System encountered an unexpected error during analysis.

**Suggested Alternatives:**
1. **Simplify your query** - Try asking about specific cancer types or treatments with simpler terms
2. **Break down complex questions** - Ask about individual aspects separately
3. **Check API status** - Our research databases may be temporarily limited

**What you can do:**
- Rephrase your question using basic cancer terminology
- Ask about specific aspects of your research interest
- Try again in a few moments

**Example simplified queries:**
- "What is lung cancer treatment?"
- "How does chemotherapy work?"
- "What are EGFR inhibitors?"

I'm designed to provide detailed technical analysis when our research tools are fully functional."""

            return chat_db.add_response(ChatMessageTemplate(
                user_id=user_id,
                chat_id=chat_id,
                sender='AI',
                content=error_response,
                additional_data={
                    "status": "failed",
                    "error": str(e),
                    "error_type": "system_error",
                    "suggestions_provided": True
                }
            ))
    
    def clear_history(self) -> bool:
        """Clear conversation history"""
        self.conversation_history = []
        return True
    
    def get_history(self) -> list:
        """Get current conversation history"""
        return self.conversation_history
    
    def get_technical_capabilities(self) -> Dict[str, List[str]]:
        """Return the technical capabilities and focus areas of this agent"""
        return {
            "research_domains": [
                "Molecular mechanisms and pathways",
                "Clinical trial analysis",
                "Biomarker research",
                "Therapeutic target identification",
                "Drug resistance mechanisms",
                "Tumor microenvironment studies",
                "Immunotherapy research",
                "Precision medicine approaches"
            ],
            "analytical_capabilities": [
                "Statistical analysis interpretation",
                "Study methodology assessment",
                "Evidence quality evaluation",
                "Cross-study synthesis",
                "Real-world evidence integration",
                "Research gap identification"
            ],
            "output_characteristics": [
                "Highly verbose and detailed responses",
                "Technical terminology usage",
                "Quantitative data inclusion",
                "Mechanistic explanations",
                "Clinical correlation analysis",
                "Source attribution and citations"
            ]
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize the agent
    research_agent = ResearchAgent()
    
    # Example technical query
    test_query = "What are the different types of lung cancer?"
    test_user = "putcZPfnudmgXrMMOG0m"
    test_chat = "research_chat"

    # Process the query
    result = research_agent.query(
        question=test_query,
        user_id=test_user,
        chat_id=test_chat
    )
    
    # print("Technical Analysis Generated:")
    # print("="*50)
    # print(result.get('content', 'No response generated'))

    from pprint import pprint
    pprint(result)