import streamlit as st
from tests.test_agent import EnhancedMedicalResearchAgent, ConversationMemory

# Set page config
st.set_page_config(page_title="OncoMind-AI", layout="wide")

# Title and description
st.title("🤖 OncoMind-AI")
st.markdown("Your intelligent assistant for cancer research and patient information.")

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = EnhancedMedicalResearchAgent()
    st.session_state.messages = []
    st.session_state.history = []

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    if st.button("Reset Conversation"):
        st.session_state.agent.reset_conversation()
        st.session_state.messages = []
        st.session_state.history = []
        st.success("Conversation reset!")

    show_history = st.toggle("Show Full Conversation History", True)
    
    st.markdown("---")
    st.header("Memory Summary")
    memory_summary = st.session_state.agent.get_memory_summary()
    st.markdown(memory_summary)

# Display chat history
if show_history:
    st.header("Conversation History")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask about cancer research, treatments, or patient experiences...")

if prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🧠 The agent is thinking..."):
            response = st.session_state.agent.chat(prompt, show_thinking=True)
            st.markdown(response)
    
    # Add agent response to history
    st.session_state.messages.append({"role": "assistant", "content": response})
