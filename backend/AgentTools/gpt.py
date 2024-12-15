from langgraph_core.agent import Agent
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict
from datetime import datetime
import re

# Import your tools
from PLOS import PLOSSearchTool, PLOSPDFDownload
from Reddit import RedditSearch
from Summarizer import summarize_pdf

# Define memory structure
class Memory:
    def __init__(self):
        self.history: List[Dict] = []
        self.tool_calls: List[Dict] = []

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

    def add_tool_call(self, tool_name, args, result):
        self.tool_calls.append({
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "args": args,
            "result": result
        })

    def get_last_tools(self):
        return self.tool_calls[-5:]

memory = Memory()

# Initialize tools
plos_search = PLOSSearchTool()
plos_pdf_download = PLOSPDFDownload()
reddit_search = RedditSearch()

def extract_keywords(query: str, max_keywords: int = 5) -> str:
    words = re.findall(r'\b\w+\b', query.lower())
    keywords = list(dict.fromkeys(words))[:max_keywords]
    return " ".join(keywords)

def reflect_and_answer(user_query: str) -> str:
    memory.add_message("user", user_query)
    
    # Step 1: Extract keywords
    keywords = extract_keywords(user_query, 5)
    
    # Step 2: Call tools
    plos_result = plos_search._run(query=keywords, max_records=5)
    memory.add_tool_call("plos_search", {"query": keywords, "max_records": 5}, plos_result)

    reddit_result = reddit_search._run(query=keywords, max_records=5, sort_by="relevance")
    memory.add_tool_call("reddit_search", {"query": keywords, "max_records": 5}, reddit_result)

    # Step 3: Analyze results
    response_parts = []
    
    if plos_result.get("status") == "success" and plos_result.get("articles"):
        response_parts.append(f"I found {len(plos_result['articles'])} research papers:")
        for article in plos_result['articles']:
            response_parts.append(f"Title: {article['title']}\nAbstract: {article['abstract'][:300]}...")
    else:
        response_parts.append("No relevant research papers found.")

    if reddit_result:
        response_parts.append(f"I also found {len(reddit_result)} user posts:")
        for post in reddit_result[:3]:  # Show top 3 only
            response_parts.append(f"Subreddit: {post['subreddit']}\nTitle: {post['title']}\nComments: {post['num_comments']}")

    # Step 4: Reflect on conflicting data
    conflicts = []
    # Example simplistic conflict detection based on presence/absence of terms
    if plos_result.get("status") == "success" and reddit_result:
        conflicts.append("Some user posts might have opinions that differ from research findings.")

    if conflicts:
        response_parts.append("\nNote: There may be conflicting information between research papers and user posts. Always consult a healthcare professional before making decisions.")

    memory.add_message("agent", "\n".join(response_parts))
    return "\n".join(response_parts)

# Agent interaction function
def handle_query(user_query: str):
    return reflect_and_answer(user_query)

# Example use case
if __name__ == "__main__":
    query = input("Ask your question about cancer: ")
    answer = handle_query(query)
    print("\n" + answer)
