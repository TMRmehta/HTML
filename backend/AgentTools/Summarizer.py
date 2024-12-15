import PyPDF2
import sys, os, io

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import tool
from google.cloud import storage

from typing import Optional, List
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Disable all gRPC logs
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"

client = storage.Client(project=os.getenv("GCP_PROJECT_ID"))
bucket = client.bucket(os.getenv("GCS_PDF_BUCKET"))

summary_model = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-lite',
    temperature=0,
    api_key=os.getenv('GEMINI_API_KEY'),
    max_tokens=1024*8
)


@tool
def summarize_pdf(pdf_path:str, max_paragraphs:Optional[int] = 3) -> str:
    """
    Opens a PDF file, reads its text content, and summarizes it.

    Args:
        pdf_path (str): The path to the PDF file.
        max_paragraphs (int): Maximum number of text paragraphs to be returned in the summary.

    Returns:
        str: A summary of the PDF content, or an error message if something goes wrong.
    """
    max_paragraphs = min(max_paragraphs, 10)

    try:
        pdf_name = os.path.basename(pdf_path)
        if not pdf_name.endswith('.pdf'):
            pdf_name = pdf_name + '.pdf'

        pdf_text = "" 
        blob = bucket.blob("GEP_model_SCLCpdf.pdf")
        pdf_bytes = blob.download_as_bytes()
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_stream)
        
        for i, page in enumerate(reader.pages):
            pdf_text += page.extract_text()

        if not pdf_text.strip():
            return "Could not extract any text from the PDF. It may be an image-based PDF or reading text is disabled."

        sys_prompt = f"""
        You are an intelligent text summarization model.
        The user will give you some text data, your task is to summarize it in upto {max_paragraphs} paragraphs. You may add extra paragraphs if the original text is too long and you need more words to generate a summary.
        Enure that you do not miss out on any important details or key findings.
        If the text data contains named entites such as authors, places or organizations, make sure you include them in the summary.
        Include the title and publication dates (if present.)
        """

        messages = [
            HumanMessage(content=sys_prompt),
            AIMessage(content=f'Sure, I will summarize the text you provide in about {max_paragraphs} paragaphs, while following the given instructions. Please provide the text that needs to be summarized.'),
            HumanMessage(content=f'Please summarize the text given below - \n\n{pdf_text}')
        ]

        response = summary_model.invoke(messages)
        return response.content

    except Exception as e:
        return f"An error occoured while trying to summarize {pdf_path} - {e}"

@tool
def list_pdfs() -> List[str]:
    """Returns:
            A list of all pdf files present in GCS bucket, an error message in a list if something goes wrong.
    """

    try:
        blobs = client.list_blobs(os.getenv("GCS_PDF_BUCKET"))
        return [item.name for item in blobs]
    
    except Exception as e:
        return [f'Failed to fetch file names from bucket - {e}']


def summarize_title(query:str):
    try:
        messages = [
            HumanMessage(f"""
                         You are a helpful summarization model. 
                         Based on the user's given question, summarize it into a title of not more than 8 words.
                         Do not return anything else, just give me the title.
                         Question: {query}
                         """)
        ]

        title = summary_model.invoke(messages).content
        return title
    
    except Exception as e:
        return f'Untitled chat {query[:30]}'


if __name__ == '__main__':
    # from pprint import pprint
    # pprint(list_pdfs())
    # print()
    # pprint(summarize_pdf("liquid_biopsy_mpspdf"))

    print(summarize_title("What are the latest advancements in lung cancer?"))