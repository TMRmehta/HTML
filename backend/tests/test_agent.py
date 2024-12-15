import os
import operator
import json
import re
from typing import TypedDict, Annotated, Literal, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI

# Import your existing tools
from AgentTools.Summarizer import summarize_pdf
from AgentTools.PLOS import PLOSSearchTool, PLOSPDFDownload
from AgentTools.Reddit import RedditSearch

# Load environment variables
load_dotenv()

# Disable gRPC logs
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    api_key=os.getenv("GOOGLE_API_KEY"),
    max_output_tokens=4096,
)

# Initialize tools
plos_search_tool = PLOSSearchTool()
plos_pdf_tool = PLOSPDFDownload()
reddit_search_tool = RedditSearch()

tools = [plos_search_tool, plos_pdf_tool, reddit_search_tool, summarize_pdf]


class ConversationMemory:
    """Manages conversation memory and retrieval of previous Q&As"""
    
    def __init__(self):
        self.qa_history: List[Dict[str, Any]] = []
        self.medical_terms: Dict[str, str] = {}
        self.evidence_base: List[Dict[str, Any]] = []
        self.pdf_summaries: Dict[str, str] = {}  # Store PDF summaries by DOI/URL
    
    def add_qa_pair(self, question: str, answer: str, sources: List[str] = None):
        """Store a question-answer pair with metadata"""
        qa_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "sources": sources or [],
            "keywords": self._extract_keywords(question)
        }
        self.qa_history.append(qa_entry)
    
    def add_evidence(self, topic: str, source: str, evidence: str, quality_score: float = 0.5):
        """Store evidence with quality assessment"""
        evidence_entry = {
            "topic": topic,
            "source": source,
            "evidence": evidence,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat()
        }
        self.evidence_base.append(evidence_entry)
    
    def add_pdf_summary(self, identifier: str, summary: str, metadata: Dict = None):
        """Store PDF summary with metadata"""
        self.pdf_summaries[identifier] = {
            "summary": summary,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
    
    def find_related_qas(self, question: str, max_results: int = 3) -> List[Dict]:
        """Find previously asked similar questions"""
        question_keywords = set(self._extract_keywords(question))
        
        scored_qas = []
        for qa in self.qa_history:
            qa_keywords = set(qa["keywords"])
            similarity = len(question_keywords.intersection(qa_keywords)) / len(question_keywords.union(qa_keywords))
            if similarity > 0.2:  # Threshold for relevance
                scored_qas.append((similarity, qa))
        
        scored_qas.sort(key=lambda x: x[0], reverse=True)
        return [qa for _, qa in scored_qas[:max_results]]
    
    def get_conflicting_evidence(self, topic: str) -> List[Dict]:
        """Find potentially conflicting evidence on a topic"""
        topic_evidence = [e for e in self.evidence_base if topic.lower() in e["topic"].lower()]
        
        # Simple conflict detection based on quality scores and contradictory keywords
        conflicting_keywords = [
            ("effective", "ineffective"), ("safe", "unsafe"), ("beneficial", "harmful"),
            ("recommended", "not recommended"), ("proven", "unproven")
        ]
        
        conflicts = []
        for i, evidence1 in enumerate(topic_evidence):
            for j, evidence2 in enumerate(topic_evidence[i+1:], i+1):
                for pos_word, neg_word in conflicting_keywords:
                    if (pos_word in evidence1["evidence"].lower() and 
                        neg_word in evidence2["evidence"].lower()) or \
                       (neg_word in evidence1["evidence"].lower() and 
                        pos_word in evidence2["evidence"].lower()):
                        conflicts.append([evidence1, evidence2])
                        break
        
        return conflicts
    
    def store_medical_term(self, term: str, definition: str):
        """Store a medical term and its simple explanation"""
        self.medical_terms[term.lower()] = definition
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        # Remove common stop words and extract meaningful terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "what", "how", "when", "where", "why"}
        words = re.findall(r'\w+', text.lower())
        return [word for word in words if word not in stop_words and len(word) > 3]


# Enhanced agent state with memory
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    thinking: Annotated[list, operator.add]
    next_action: str
    memory: ConversationMemory
    current_evidence: Annotated[list, operator.add]
    medical_terms_found: Annotated[list, operator.add]
    pdf_urls: Annotated[list, operator.add]  # Store PDF URLs for downloading


def extract_medical_terms(text: str) -> List[str]:
    """Extract potential medical terms from text"""
    # Common medical term patterns
    medical_patterns = [
        r'\b[A-Z][a-z]+oma\b',  # tumors ending in -oma
        r'\b[A-Z][a-z]+itis\b',  # inflammation ending in -itis  
        r'\b[A-Z][a-z]+osis\b',  # conditions ending in -osis
        r'\b[A-Z][a-z]+therapy\b',  # therapies
        r'\b[A-Z][a-z]+carcinoma\b',  # carcinomas
        r'\b[A-Z][a-z]+sarcoma\b',  # sarcomas
    ]
    
    # Medical abbreviations and technical terms
    common_medical_terms = [
        'chemotherapy', 'radiotherapy', 'immunotherapy', 'metastasis', 'oncology',
        'biopsy', 'prognosis', 'diagnosis', 'benign', 'malignant', 'tumor', 'cancer',
        'lymphoma', 'leukemia', 'melanoma', 'carcinogen', 'palliative', 'adjuvant',
        'neoadjuvant', 'remission', 'relapse', 'staging', 'biomarker'
    ]
    
    found_terms = []
    text_lower = text.lower()
    
    # Check for pattern-based terms
    for pattern in medical_patterns:
        matches = re.findall(pattern, text)
        found_terms.extend(matches)
    
    # Check for common medical terms
    for term in common_medical_terms:
        if term in text_lower:
            found_terms.append(term)
    
    return list(set(found_terms))  # Remove duplicates


def extract_pdf_urls_from_plos_results(search_results: str) -> List[str]:
    """Extract PDF URLs from PLOS search results"""
    pdf_urls = []
    
    # Look for DOI patterns in the search results
    doi_pattern = r'10\.1371/journal\.[a-z]+\.\d+'
    dois = re.findall(doi_pattern, search_results)
    
    # Convert DOIs to PDF URLs
    for doi in dois[:3]:  # Limit to first 3 papers
        pdf_url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable"
        pdf_urls.append(pdf_url)
    
    # Also look for direct PDF URLs in the results
    pdf_url_pattern = r'https://[^\s]+\.pdf'
    direct_pdfs = re.findall(pdf_url_pattern, search_results)
    pdf_urls.extend(direct_pdfs[:2])  # Add up to 2 direct PDF URLs
    
    return list(set(pdf_urls))  # Remove duplicates


def explain_medical_terms_node(state: AgentState) -> dict:
    """Node to identify medical terms in user query and add to state"""
    messages = state["messages"]
    
    # Get the latest user message
    user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    if not user_messages:
        return {"medical_terms_found": []}
    
    latest_message = user_messages[-1].content
    medical_terms = extract_medical_terms(latest_message)
    
    return {"medical_terms_found": list(set(medical_terms))}


def memory_retrieval_node(state: AgentState) -> dict:
    """Retrieve relevant previous conversations"""
    messages = state["messages"]
    memory = state["memory"]
    
    user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    if not user_messages:
        return {"thinking": ["No previous context to retrieve"]}
    
    latest_question = user_messages[-1].content
    related_qas = memory.find_related_qas(latest_question)
    
    thinking_additions = []
    if related_qas:
        thinking_additions.append("🧠 **Related Previous Conversations Found:**")
        for qa in related_qas:
            thinking_additions.append(f"- Q: {qa['question'][:100]}...")
            thinking_additions.append(f"  A: {qa['answer'][:150]}...")
    else:
        thinking_additions.append("🧠 **No related previous conversations found**")
    
    return {
        "thinking": thinking_additions,
        "memory": memory
    }


def evidence_analysis_node(state: AgentState) -> dict:
    """Analyze and compare evidence for conflicts"""
    current_evidence = state.get("current_evidence", [])
    memory = state["memory"]
    thinking_additions = []
    
    if len(current_evidence) < 2:
        return {"thinking": ["Not enough evidence to compare"]}
    
    # Simple conflict detection
    evidence_texts = [str(evidence) for evidence in current_evidence]
    
    conflict_analysis_prompt = f"""
    Analyze the following evidence for potential conflicts or contradictions:
    
    Evidence pieces:
    {chr(10).join([f"{i+1}. {evidence}" for i, evidence in enumerate(evidence_texts)])}
    
    Identify:
    1. Any direct contradictions between evidence pieces
    2. Different quality levels of evidence (peer-reviewed vs anecdotal)
    3. Different contexts that might explain apparent conflicts
    4. Overall consensus if one exists
    
    Provide a brief analysis focusing on what patients/families should know about conflicting information.
    """
    
    analysis_response = llm.invoke([SystemMessage(content=conflict_analysis_prompt)])
    
    thinking_additions.append("⚖️ **Evidence Analysis:**")
    thinking_additions.append(analysis_response.content)
    
    return {
        "thinking": thinking_additions,
        "memory": memory
    }


def enhanced_thinking_node(state: AgentState) -> dict:
    """Enhanced thinking node with memory awareness"""
    messages = state["messages"]
    memory = state["memory"]
    
    # Get related previous conversations
    user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    related_context = ""
    if user_messages:
        related_qas = memory.find_related_qas(user_messages[-1].content)
        if related_qas:
            related_context = f"\nRelated previous conversations:\n{json.dumps(related_qas[:2], indent=2)}"

    thinking_prompt = f"""
    You are a medical research assistant agent. Analyze the current conversation and think about what you need to do next.

    Current conversation:
    {messages}
    
    {related_context}

    Available tools:
    1. plos_search - Search for research papers in PLOS database
    2. plos_pdf_downloader - Download PDF files from PLOS articles
    3. reddit_search - Search Reddit posts in medical subreddits
    4. summarize_pdf - Summarize PDF content

    Think step by step:
    1. What is the user asking for?
    2. Have I answered similar questions before? (check related context)
    3. Do I have enough information to answer directly?
    4. What tools (if any) should I use to gather more information?
    5. Should I search for papers first, then download and analyze the most relevant PDFs?
    6. Are there any medical terms I should explain?
    7. What's my strategy to provide the best evidence-based answer?
    
    For medical questions, prioritize getting research evidence by:
    1. First searching PLOS database for relevant papers
    2. Then downloading and analyzing the most relevant PDFs
    3. Optionally checking Reddit for patient perspectives
    """

    thinking_response = llm.invoke(thinking_prompt)

    return {
        "thinking": [f"🤔 **Agent Thinking**: {thinking_response.content}"],
        "next_action": "memory_check",
    }


def decision_node(state: AgentState) -> dict:
    messages = state["messages"]
    current_evidence = state.get("current_evidence", [])
    pdf_urls = state.get("pdf_urls", [])

    decision_prompt = f"""
    Based on the conversation and evidence gathered so far, decide what to do next:

    Current evidence count: {len(current_evidence)}
    PDF URLs available: {len(pdf_urls)}

    Options:
    1. "search_papers" - If you need to search for research papers first
    2. "download_pdf" - If you have PDF URLs and need to download/analyze them
    3. "search_reddit" - If you need patient experiences/discussions
    4. "respond" - If you have enough information to answer the user

    Decision logic:
    - If no evidence yet: start with "search_papers"
    - If you have search results but no PDF analysis: use "download_pdf" 
    - If you have good evidence but want patient perspectives: use "search_reddit"
    - If you have sufficient evidence from papers: use "respond"

    Respond with ONLY one of these four options.
    """

    decision_response = llm.invoke(messages + [SystemMessage(content=decision_prompt)])
    next_action = decision_response.content.strip().lower()

    valid_actions = ["search_papers", "search_reddit", "download_pdf", "respond"]
    if next_action not in valid_actions:
        # Default logic based on current state
        if len(current_evidence) == 0:
            next_action = "search_papers"
        elif pdf_urls and not any("PDF Analysis" in str(evidence) for evidence in current_evidence):
            next_action = "download_pdf"
        else:
            next_action = "respond"

    return {"next_action": next_action}


def enhanced_tool_calling_node(state: AgentState) -> dict:
    """Enhanced tool calling with evidence storage and PDF processing"""
    messages = state["messages"]
    next_action = state["next_action"]
    memory = state["memory"]
    current_evidence = []
    pdf_urls = []

    if next_action == "search_papers":
        query_prompt = """
        Based on the user's question, extract 3-5 relevant keywords for searching medical research papers.
        Focus on the main medical condition, treatment, or topic.
        Return ONLY the keywords separated by spaces, no other text.
        """
        query_response = llm.invoke(messages + [SystemMessage(content=query_prompt)])
        search_query = query_response.content.strip()

        try:
            search_results = plos_search_tool._run(query=search_query, max_records=5)
            
            # Extract PDF URLs from search results
            pdf_urls = extract_pdf_urls_from_plos_results(search_results)
            
            # Store evidence in memory
            memory.add_evidence(
                topic=search_query,
                source="PLOS Database",
                evidence=search_results,
                quality_score=0.8  # High quality for peer-reviewed papers
            )
            
            current_evidence.append({
                "source": "PLOS Database",
                "content": search_results,
                "quality": "high"
            })

            tool_message = ToolMessage(
                content=f"📚 **Research Papers Found**: {search_results}",
                tool_call_id="plos_search",
            )

            return {
                "messages": [tool_message],
                "thinking": [f"🔍 **Searched PLOS database** for: '{search_query}'. Found {len(pdf_urls)} PDFs to analyze."],
                "next_action": "decide",
                "memory": memory,
                "current_evidence": current_evidence,
                "pdf_urls": pdf_urls
            }
        
        except Exception as e:
            return {
                "thinking": [f"❌ **Error searching PLOS database**: {str(e)}"],
                "next_action": "respond"
            }

    elif next_action == "download_pdf":
        pdf_urls = state.get("pdf_urls", [])
        
        if not pdf_urls:
            return {
                "thinking": ["⚠️ **No PDF URLs available for download**"],
                "next_action": "respond"
            }
        
        pdf_summaries = []
        processed_pdfs = 0
        
        for pdf_url in pdf_urls[:2]:  # Limit to 2 PDFs to avoid timeout
            try:
                # Download PDF
                download_result = plos_pdf_tool._run(url=pdf_url)
                
                if download_result and "successfully" in download_result.lower():
                    # Extract filename from download result
                    filename_match = re.search(r'([^/]+\.pdf)', download_result)
                    if filename_match:
                        pdf_filename = filename_match.group(1)
                        
                        # Summarize the PDF
                        summary_result = summarize_pdf._run(pdf_path=pdf_filename)
                        
                        if summary_result:
                            pdf_summaries.append(f"**PDF Analysis {processed_pdfs + 1}**:\n{summary_result}")
                            
                            # Store in memory
                            memory.add_pdf_summary(
                                identifier=pdf_url,
                                summary=summary_result,
                                metadata={"url": pdf_url, "filename": pdf_filename}
                            )
                            
                            processed_pdfs += 1
                
            except Exception as e:
                pdf_summaries.append(f"**PDF Analysis Error**: Could not process {pdf_url}: {str(e)}")
        
        if pdf_summaries:
            combined_summaries = "\n\n".join(pdf_summaries)
            
            # Store as high-quality evidence
            memory.add_evidence(
                topic="PDF Analysis",
                source="Research Paper Analysis",
                evidence=combined_summaries,
                quality_score=0.9  # Highest quality for full paper analysis
            )
            
            current_evidence.append({
                "source": "PDF Analysis",
                "content": combined_summaries,
                "quality": "highest"
            })
            
            tool_message = ToolMessage(
                content=f"📄 **PDF Analysis Complete**: {combined_summaries}",
                tool_call_id="pdf_analysis",
            )
            
            return {
                "messages": [tool_message],
                "thinking": [f"📄 **Analyzed {processed_pdfs} research papers** for detailed evidence"],
                "next_action": "decide",
                "memory": memory,
                "current_evidence": current_evidence
            }
        else:
            return {
                "thinking": ["❌ **Could not process any PDFs**"],
                "next_action": "respond"
            }

    elif next_action == "search_reddit":
        query_prompt = """
        Based on the user's question, extract 3-5 relevant keywords for searching Reddit discussions.
        Focus on patient experiences and real-world perspectives.
        Return ONLY the keywords separated by spaces, no other text.
        """
        query_response = llm.invoke(messages + [SystemMessage(content=query_prompt)])
        search_query = query_response.content.strip()

        try:
            search_results = reddit_search_tool._run(query=search_query, max_records=3)
            
            # Store evidence in memory  
            memory.add_evidence(
                topic=search_query,
                source="Reddit Discussions",
                evidence=search_results,
                quality_score=0.3  # Lower quality for anecdotal evidence
            )
            
            current_evidence.append({
                "source": "Reddit Discussions", 
                "content": search_results,
                "quality": "low"
            })

            tool_message = ToolMessage(
                content=f"💬 **Reddit Discussions Found**: {search_results}",
                tool_call_id="reddit_search",
            )

            return {
                "messages": [tool_message],
                "thinking": [f"🔍 **Searched Reddit** for: '{search_query}'"],
                "next_action": "analyze_evidence",
                "memory": memory,
                "current_evidence": current_evidence
            }
        
        except Exception as e:
            return {
                "thinking": [f"❌ **Error searching Reddit**: {str(e)}"],
                "next_action": "respond"
            }

    else:
        return {"next_action": "respond"}


def enhanced_response_node(state: AgentState) -> dict:
    """Enhanced response with memory storage and medical term explanations"""
    messages = state["messages"]
    memory = state["memory"]
    query_medical_terms = state.get("medical_terms_found", [])
    current_evidence = state.get("current_evidence", [])

    # Check for conflicting evidence
    conflict_analysis = ""
    if len(current_evidence) > 1:
        conflicts = memory.get_conflicting_evidence("current_topic")
        if conflicts:
            conflict_analysis = "\n\n⚠️ **Note**: I found some potentially conflicting information. This is common in medical research where studies may have different methodologies, sample sizes, or focus on different populations. Always consult with healthcare professionals for personalized advice."

    # Prepare evidence summary for the system prompt
    evidence_summary = ""
    if current_evidence:
        evidence_summary = "\n\nEvidence sources used in this response:\n"
        for i, evidence in enumerate(current_evidence, 1):
            evidence_summary += f"{i}. {evidence['source']} (Quality: {evidence['quality']})\n"

    system_prompt = f"""
    You are a friendly and empathetic medical research assistant, OncoMind-AI. Your goal is to provide accurate, helpful, and easy-to-understand information about medical topics, particularly cancer-related questions.

    Your tone should be supportive, caring, and conversational. Imagine you are talking to a patient or their family member who may be feeling overwhelmed.

    Guidelines:
    - Start your response with a warm and reassuring tone.
    - Provide evidence-based information, synthesizing from all available sources.
    - Ground your response in the research evidence that was gathered, especially PDF analyses.
    - Explain complex findings in simple terms.
    - Be very clear about the limitations of the information and strongly advise consulting with healthcare professionals for medical advice.
    - Acknowledge the sources you used and explain their quality levels.
    - When there's conflicting evidence, acknowledge it gently and explain that this is common in research.
    - End your response with the standard medical disclaimer.

    {evidence_summary}

    {conflict_analysis}

    Remember to be a helpful and kind guide who bases responses on solid research evidence.
    The disclaimer is: "This is for informational purposes only and should not replace professional medical advice."
    """

    response = llm.invoke([SystemMessage(content=system_prompt)] + messages)
    
    # Store the Q&A in memory
    user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    if user_messages:
        sources = [evidence['source'] for evidence in current_evidence]
        memory.add_qa_pair(
            question=user_messages[-1].content,
            answer=response.content,
            sources=sources
        )
    
    # Extract and explain medical terms from the agent's response
    response_medical_terms = extract_medical_terms(response.content)
    all_terms = list(set(query_medical_terms + response_medical_terms))
    
    explanations = []
    if all_terms:
        for term in all_terms:
            # Check if we already have an explanation
            if term.lower() in memory.medical_terms:
                explanation = memory.medical_terms[term.lower()]
            else:
                # Generate a simple explanation using proper message format
                explanation_prompt = f"Explain the medical term '{term}' in simple, everyday language that a non-medical person can understand. Keep it to 1-2 sentences maximum. Focus on what it means practically for a patient or their family."
                
                explanation_response = llm.invoke([
                    SystemMessage(content="You are a medical educator who explains complex terms in simple language."),
                    HumanMessage(content=explanation_prompt)
                ])
                explanation = explanation_response.content.strip()
                memory.store_medical_term(term, explanation)
            
            explanations.append(f"**{term.capitalize()}**: {explanation}")
            
    # Combine response with medical term explanations
    full_response_parts = [response.content]
    
    if explanations:
        full_response_parts.append("\n\n---\n")
        full_response_parts.append("📖 **Medical Terms Explained**:")
        full_response_parts.append("\n".join(explanations))
        
    full_response = "\n".join(full_response_parts)

    return {
        "messages": [AIMessage(content=full_response)],
        "thinking": ["✅ **Generated evidence-based response with medical term explanations**"],
        "memory": memory
    }


def should_continue(state: AgentState) -> Literal["thinking", "memory_retrieval", "medical_terms", "decision", "tools", "evidence_analysis", "respond", END]:
    next_action = state.get("next_action", "")

    if next_action == "memory_check":
        return "memory_retrieval"
    elif next_action == "decide":
        return "decision"
    elif next_action in ["search_papers", "search_reddit", "download_pdf"]:
        return "tools"
    elif next_action == "analyze_evidence":
        return "evidence_analysis"
    elif next_action == "medical_terms":
        return "medical_terms"
    elif next_action == "respond":
        return "respond"
    else:
        return "thinking"


# Build the enhanced graph
workflow = StateGraph(AgentState)
workflow.add_node("thinking", enhanced_thinking_node)
workflow.add_node("memory_retrieval", memory_retrieval_node)
workflow.add_node("medical_terms", explain_medical_terms_node)
workflow.add_node("decision", decision_node)
workflow.add_node("tools", enhanced_tool_calling_node)
workflow.add_node("evidence_analysis", evidence_analysis_node)
workflow.add_node("respond", enhanced_response_node)

workflow.set_entry_point("thinking")
workflow.add_conditional_edges("thinking", should_continue)
workflow.add_edge("memory_retrieval", "medical_terms")
workflow.add_edge("medical_terms", "decision")
workflow.add_conditional_edges("decision", should_continue)
workflow.add_conditional_edges("tools", should_continue)
workflow.add_edge("evidence_analysis", "respond")
workflow.add_edge("respond", END)

app = workflow.compile()


class EnhancedMedicalResearchAgent:
    def __init__(self):
        self.app = app
        self.memory = ConversationMemory()
        self.conversation_state = {
            "messages": [],
            "thinking": [],
            "next_action": "",
            "memory": self.memory,
            "current_evidence": [],
            "medical_terms_found": [],
            "pdf_urls": []
        }

    def chat(self, user_message: str, show_thinking: bool = True) -> str:
        self.conversation_state["messages"].append(HumanMessage(content=user_message))
        result = self.app.invoke(self.conversation_state)
        self.conversation_state = result

        response_parts = []
        if show_thinking and result.get("thinking"):
            response_parts.append("## Agent's Reasoning Process:")
            for thought in result["thinking"]:
                response_parts.append(thought)
            response_parts.append("\n---\n")

        ai_messages = [
            msg for msg in result["messages"] if isinstance(msg, AIMessage)
        ]
        if ai_messages:
            response_parts.append("## Response:")
            response_parts.append(ai_messages[-1].content)

        return "\n".join(response_parts)

    def get_memory_summary(self) -> str:
        """Get a summary of the agent's memory"""
        qa_count = len(self.memory.qa_history)
        terms_count = len(self.memory.medical_terms)
        evidence_count = len(self.memory.evidence_base)
        pdf_count = len(self.memory.pdf_summaries)
        
        return f"""
## Memory Summary:
- **Previous Q&As**: {qa_count}
- **Medical terms learned**: {terms_count}
- **Evidence pieces stored**: {evidence_count}
- **PDFs analyzed**: {pdf_count}
        """

    def reset_conversation(self):
        # Keep the memory but reset the conversation
        self.conversation_state = {
            "messages": [],
            "thinking": [],
            "next_action": "",
            "memory": self.memory,  # Preserve memory across resets
            "current_evidence": [],
            "medical_terms_found": [],
            "pdf_urls": []
        }


def main():
    print("🏥 Enhanced Medical Research Agent with PDF Grounding")
    print("=" * 60)
    print("Ask me about medical research, cancer treatments, or any health-related topics!")
    print("I will search research papers, download and analyze PDFs, check Reddit discussions,")
    print("remember our conversations, and explain medical terms in simple language.")
    print("Type 'quit' to exit, 'reset' to start new conversation, 'memory' to see memory summary.")
    print("=" * 60)

    agent = EnhancedMedicalResearchAgent()

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye! Stay healthy!")
                break
            elif user_input.lower() == "reset":
                agent.reset_conversation()
                print("🔄 Conversation reset. Memory preserved. How can I help you?")
                continue
            elif user_input.lower() == "memory":
                print(agent.get_memory_summary())
                continue
            elif not user_input:
                continue

            print(f"\n🤖 Agent: Processing your question...")
            response = agent.chat(user_input, show_thinking=True)
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye! Stay healthy!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again or reset the conversation.")


if __name__ == "__main__":
    agent = EnhancedMedicalResearchAgent()
    print("🧪 Testing the enhanced agent...")
    test_response = agent.chat(
        "What are the latest treatments for lung cancer?", show_thinking=True
    )
    print(test_response)