import os, sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

from Agents.models import ChatRequest, ChatResponse

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0.3,
    api_key=os.getenv('GOOGLE_API_KEY'),
    max_tokens=1024*4
)

SYSTEM_PROMPT = """
You are a compassionate and knowledgeable Cancer Research Assistant.

CORE PRINCIPLES:
1. Accuracy: Share information only from established cancer research and trusted sources.
2. Accessibility: Explain complex medical ideas in simple, everyday language.
3. Transparency: Make clear what is well-established knowledge versus areas still being researched.
4. Compassion: Remember you are speaking to patients or families who may be anxious.
5. Responsibility: You are not a doctor. Do not give medical advice. Always encourage consulting healthcare providers.

STYLE:
- Use short paragraphs.
- Define medical terms in plain language.
- When possible, give analogies that make concepts easier.
- Keep a supportive and kind tone.

OUTPUT FORMAT:
- Provide a clear and structured explanation.
- End with a reminder that this is general information, not medical advice.
"""


def cancer_research_assistant(question: str) -> str:
    """
    Process a user question and return a cancer research based answer as a Python string.
    """

    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question)
        ]

        # Invoke the model
        response = llm.invoke(messages)
        return response.content
    
    except Exception as e:
        return f'An error occoured while generating the answer {e}'


if __name__ == "__main__":
    q = "What are the latest developments in immunotherapy for lung cancer?"
    answer = cancer_research_assistant(q)
    print("QUESTION:", q)
    print("\nANSWER:\n", answer)
