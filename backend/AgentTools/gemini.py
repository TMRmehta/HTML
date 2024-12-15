import os
import operator
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers.tool_calling import ToolCallingParser

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

# --- Import your custom tools ---
# Ensure PLOS.py, Reddit.py, and Summarizer.py are in the same directory
from PLOS import PLOSSearchTool, PLOSPDFDownload
from Reddit import RedditSearch
from Summarizer import summarize_pdf

# --- Environment and Tool Setup ---
load_dotenv()

# Instantiate all the tools the agent can use
tools = [
    PLOSSearchTool(),
    PLOSPDFDownload(),
    RedditSearch(),
    summarize_pdf, # This is already decorated with @tool
]

# Create a ToolExecutor to easily call the tools by name
tool_executor = ToolExecutor(tools)

# --- LLM and Prompt Setup ---

# Use a powerful model for the main agent logic
# Gemini 1.5 Pro is excellent for complex reasoning and tool use
model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0,
    convert_system_message_to_human=True # For compatibility with older models if needed
)

# Bind the tools to the model, so it knows what functions it can call
model_with_tools = model.bind_tools(tools)

# Define the system prompt to guide the agent's behavior
# This is where we enforce all the user's rules
system_prompt = """
You are a specialized AI assistant for cancer patients and their families. Your primary goal is to provide clear, easy-to-understand, and well-sourced information about cancer research and public sentiment.

**Your Core Directives:**
1.  **Grounding is Mandatory:** You MUST base all your answers on the information retrieved from the provided tools (PLOS for research, Reddit for public discussions). NEVER generate answers from your own internal knowledge.
2.  **No Hallucination:** If the tools do not provide sufficient information to answer a question, you must explicitly state that you could not find the relevant information. Do not invent facts or details.
3.  **Simplicity is Key:** Explain complex medical and scientific concepts in simple terms that a non-expert can easily understand. Use analogies where helpful.
4.  **Tool Usage Strategy:**
    - When searching, use a maximum of 5 focused keywords for both PLOS and Reddit to get relevant results.
    - You can and should call tools multiple times if the initial results are insufficient. For example, you can search PLOS, then search Reddit for patient experiences on the same topic.
    - If you find conflicting information (e.g., a research paper says one thing, and Reddit posts say another), you should present both viewpoints and explain the potential reasons for the discrepancy (e.g., "The clinical trial showed this result, but some patients on Reddit report experiencing these side effects...").
5.  **Maintain Context:** Remember the conversation history to provide relevant follow-up answers.
"""

# Create the agent prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Create the main agent runnable chain
agent_runnable = prompt | model_with_tools


# --- Graph State Definition ---

# This TypedDict defines the structure of our agent's state.
# It's what gets passed between the nodes of the graph.
class AgentState(TypedDict):
    # The 'operator.add' ensures that new messages are appended to the list,
    # building up the history of the conversation.
    messages: Annotated[list, operator.add]


# --- Node Definitions ---
# Each node in our graph is a function that takes the state and returns a
# dictionary to update the state.

def agent_node(state: AgentState):
    """
    The core agent node. It decides whether to call a tool or respond to the user.
    """
    print("---AGENT---")
    response = agent_runnable.invoke(state)
    return {"messages": [response]}

def tool_node(state: AgentState):
    """
    This node executes the tools called by the agent.
    """
    print("---TOOLS---")
    # The last message in the state is the AI's tool call
    tool_calls = state["messages"][-1].tool_calls
    tool_messages = []
    
    if tool_calls:
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            print(f"Invoking tool: {tool_name} with args: {tool_call.get('args')}")
            # Execute the tool and get the output
            output = tool_executor.invoke(tool_call)
            # Create a ToolMessage to represent the tool's output
            tool_messages.append(
                ToolMessage(content=str(output), tool_call_id=tool_call.get("id"))
            )
        return {"messages": tool_messages}
    return {} # No tools were called

def reflection_node(state: AgentState):
    """
    This node reflects on the tool results to decide if the information is sufficient.
    It guides the agent's next step.
    """
    print("---REFLECT---")
    # Get the original user query
    initial_user_query = state['messages'][0].content
    # Get the last set of tool outputs
    last_tool_outputs = [msg.content for msg in state['messages'] if isinstance(msg, ToolMessage)]

    reflection_prompt = f"""
    You are a research strategist. Your task is to analyze the results from tool calls and guide the next action for an AI agent.
    The original user query was: "{initial_user_query}"
    The latest tool outputs are:
    ---
    {last_tool_outputs}
    ---
    Based on this, is the information sufficient to answer the user's query comprehensively and simply?
    
    - If YES, respond with only the word "PROCEED".
    - If NO, provide a brief, strategic suggestion for the next tool call. For example: "The Reddit posts mention 'immunotherapy side effects'. We should search PLOS for 'immunotherapy adverse events in lung cancer' to get clinical data."
    - If the results are contradictory, explain the conflict and suggest how to address it. For example: "The PLOS article shows a 70% success rate, but Reddit users report severe side effects. Search Reddit for specific side effect management strategies."
    - If the tools failed or returned no results, suggest an alternative search query. For example: "The PLOS search for 'new chemo drug X' yielded nothing. Try searching for its generic name or the clinical trial ID if available."
    """
    
    reflection_model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
    reflection = reflection_model.invoke(reflection_prompt).content
    
    print(f"Reflection: {reflection}")

    # If the reflection is to proceed, we let the agent generate the final answer.
    # Otherwise, we add the reflection as a new instruction to guide the next agent loop.
    if "PROCEED" in reflection.upper():
        return {"messages": [HumanMessage(content="The user's query can now be answered based on the gathered information. Generate the final, comprehensive response.")]}
    else:
        # This message guides the next iteration of the agent_node
        return {"messages": [HumanMessage(content=f"Reflection on previous step: {reflection}. Continue working to satisfy the user's request.")]}


# --- Conditional Edge Logic ---

def should_continue(state: AgentState) -> str:
    """
    Determines the next step after the agent node.
    If the agent called tools, we go to the tool node.
    Otherwise, we end the process.
    """
    if state["messages"][-1].tool_calls:
        return "continue_to_tools"
    else:
        return "end"

# --- Graph Construction ---

# 1. Initialize the StateGraph with our AgentState
graph = StateGraph(AgentState)

# 2. Add the nodes to the graph
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_node("reflection", reflection_node)

# 3. Set the entry point of the graph
graph.set_entry_point("agent")

# 4. Add the conditional edge from the agent
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue_to_tools": "tools",
        "end": END,
    },
)

# 5. Add the regular edges for the main ReAct loop
graph.add_edge("tools", "reflection")
graph.add_edge("reflection", "agent")

# 6. Compile the graph into a runnable application
app = graph.compile()


# --- Main Execution Block ---

if __name__ == "__main__":
    print("Welcome to the Cancer Research AI Assistant.")
    print("You can ask questions about cancer research papers from PLOS or public discussions on Reddit.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("-" * 50)

    # Maintain conversation history
    history = []
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Append the new user message to the history
        history.append(HumanMessage(content=user_input))

        # The input to the graph is the entire message history
        inputs = {"messages": history}
        
        final_response = None
        
        # Stream the graph execution to see the agent's thought process
        print("\n🤖 Assistant is thinking...\n")
        for event in app.stream(inputs):
            for key, value in event.items():
                if key == "agent" and value.get('messages'):
                    # The agent's message might be a tool call or a final answer
                    last_message = value['messages'][-1]
                    if not last_message.tool_calls:
                         final_response = last_message.content
                print("---")
        
        if final_response:
            print(f"\nAssistant:\n{final_response}\n")
            # Append the final AI response to the history
            history.append(AIMessage(content=final_response))
        else:
            print("\nAssistant: I seem to have completed my tool usage but didn't generate a final response. Let's try again.\n")