import sys, os, requests

from pydantic import BaseModel, Field
from google.cloud import storage
from dotenv import load_dotenv
from langchain.tools import BaseTool


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Init GCS Bucket
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

client = storage.Client(project=os.getenv('GCP_PROJECT_ID'))
bucket_name = os.getenv('GCS_PDF_BUCKET')
bucket = client.bucket(bucket_name)


class PLOSSearchInput(BaseModel):
    query: str = Field(description='Search query, upto 5 relevant keywords')
    max_records: int = Field(description='Maximum number of records to fetch', default=10)


class PLOSSearchTool(BaseTool):
    name: str = 'plos_search'
    description: str = 'Download research papers/articles metadata from PLOS database.'
    args_schema: type[BaseModel] = PLOSSearchInput
    
    def _run(self, query: str, max_records: int) -> dict:
        if max_records > 20:
            max_records = 20
        try:
            params = {
                "q": query,
                "wt": "json",
                "rows": int(max_records),
                "fl": "id,title,author_display,abstract,pub_date,journal"
            }
            response = requests.get("http://api.plos.org/search", params=params)
            response.raise_for_status()
            
            docs = response.json()["response"]["docs"]
            if not docs:
                return {
                    "status": "failed",
                    "message": f"No relevant data for query '{query}'"
                }
            
            # Process and structure the results
            results = []
            for item in docs:
                results.append({
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "authors": item.get("author_display", []),
                    "abstract": item.get("abstract", ""),
                    "publication_date": item.get("pub_date", ""),
                    "journal": item.get("journal", "")
                })
            
            return {
                "status": "success",
                "count": len(results),
                "articles": results
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error while fetching results from PLOS - {e}"
            }


class PLOSPDFInput(BaseModel):
    article_id: str = Field(description='id of the article')
    filename: str = Field(description='name for the downloaded pdf file, all downloaded files are saved in plos_pdf folder by default')


class PLOSPDFDownload(BaseTool):
    name: str = 'plos_pdf_downloader'
    description: str = 'Download PDF file for PLOS papers/articles and save them to plos_pdf folder.'
    args_schema: type[BaseModel] = PLOSPDFInput
    
    def _run(self, article_id: str, filename: str) -> dict:
        # os.makedirs('plos_pdf', exist_ok=True)
        pdf_url = f"https://journals.plos.org/plosone/article/file?id={article_id}&type=printable"
        
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Clean filename to avoid issues
                # os.makedirs('plos_pdf', exist_ok=True)
                clean_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                # path = os.path.join("plos_pdf", f"{clean_filename}.pdf")
                
                # with open(path, "wb") as f:
                #     f.write(response.content)

                # Also save to GCS
                gcs_path = f'{clean_filename}.pdf'
                blob = bucket.blob(gcs_path)
                blob.upload_from_string(response.content, content_type='application/pdf')

                return {
                    "download_status": "Success",
                    "filename": clean_filename,
                    "article_id": article_id,
                    "file_path": "oncosight-pdf-bucket",
                    "file_size": len(response.content)
                }
            
            else:
                return {
                    "download_status": f"Failed, HTTP code {response.status_code}",
                    "filename": filename,
                    "article_id": article_id
                }
                
        except Exception as e:
            return {
                "download_status": f"Failed, exception occurred - {e}",
                "filename": filename,
                "article_id": article_id
            }


# Test Code
if __name__ == "__main__":
    search = PLOSSearchTool()
    result = search._run(query='lung_cancer', max_records=2)
    print(result)

    downloader = PLOSPDFDownload()
    result = downloader._run(article_id='10.1371/journal.pmed.0030091', filename='Five Glutathione S-Transferase Gene Variants.pdf')
    print(result)