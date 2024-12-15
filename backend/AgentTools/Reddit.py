import sys, os, json, praw, hashlib
from time import time, sleep
from pydantic import BaseModel, Field, field_validator
from langchain.tools import BaseTool
from dotenv import load_dotenv
from pathlib import Path
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Constants
INVOKE_DELAY: int = 10
INTERVAL_DELAY: float = 0.05
ALLOWED_SUBREDDITS: List[str] = ["cancer", "AskScience", "medicalresearch", "AskDocs", "Medical_Students", "medicine"]
SORT_TYPES: List[str] = ["relevance", "hot", "top", "new", "comments"]

# PRAW client
reddit_client: praw.Reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)


class RedditSearchInput(BaseModel):
    query: str = Field(description='Search query consisting of up to 8 relevant keywords')
    subreddit: str = Field(
        description=f'Single subreddit to search. Choose from: {", ".join(ALLOWED_SUBREDDITS)}', 
        default='cancer'
    )
    max_records: int = Field(
        description='Maximum number of posts to fetch (max 10)', 
        default=3
    )
    sort_by: str = Field(
        description=f'Sorting method. Options: {", ".join(SORT_TYPES)}', 
        default='relevance'
    )

    @field_validator('max_records')
    @classmethod
    def max_records_must_be_in_range(cls, v):
        if v > 10:
            return 10
        return max(1, v)  # Ensure at least 1

    @field_validator('subreddit')
    @classmethod
    def subreddit_must_be_allowed(cls, v):
        if v not in ALLOWED_SUBREDDITS:
            raise ValueError(f'Subreddit must be one of: {ALLOWED_SUBREDDITS}')
        return v
    
    @field_validator('sort_by')
    @classmethod
    def sort_by_must_be_valid(cls, v):
        if v not in SORT_TYPES:
            raise ValueError(f'sort_by must be one of {SORT_TYPES}')
        return v


class RedditSearch(BaseTool):
    name: str = 'reddit_search'
    description: str = 'Search for relevant reddit posts based on given keywords in a specific subreddit. Useful for finding patient experiences and community discussions about medical topics.'
    args_schema: type[BaseModel] = RedditSearchInput
    results: List[dict] = []
    last_invoke: float = 0
    _cache: dict = {}

    def _generate_cache_key(self, query: str, subreddit: str, max_records: int, sort_by: str) -> str:
        """Generates a unique cache key for a search."""
        unique_string = f"{query}-{subreddit}-{max_records}-{sort_by}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _get_cached_results(self, cache_key: str) -> List[dict] | None:
        """Gets cached results from in-memory cache."""
        if cache_key in self._cache:
            return self._cache[cache_key]
        return None

    def _cache_results(self, cache_key: str, results: List[dict]):
        """Saves search results to the in-memory cache."""
        self._cache[cache_key] = results

    def _run(self, query: str, subreddit: str = 'cancer', max_records: int = 5, sort_by: str = 'relevance') -> str:
        """
        Search Reddit for posts matching the query in the specified subreddit.
        
        Args:
            query: Search terms to look for
            subreddit: Single subreddit to search in
            max_records: Maximum number of posts to return
            sort_by: How to sort the results
            
        Returns:
            JSON string containing search results
        """
        
        # Generate cache key and check for cached results
        cache_key = self._generate_cache_key(query, subreddit, max_records, sort_by)
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            return json.dumps(cached_results)

        self.results = []
        current_time = time()

        # Rate limiting
        if (current_time - self.last_invoke) < INVOKE_DELAY:
            sleep(INVOKE_DELAY - (current_time - self.last_invoke))

        try:
            print(f"Searching in r/{subreddit} for '{query}' sorted by '{sort_by}'...")
            subreddit_obj = reddit_client.subreddit(subreddit)
            
            for post in subreddit_obj.search(query, sort=sort_by, limit=max_records):
                post_data = {
                    "subreddit": subreddit,
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                    "selftext": post.selftext[:500] if post.selftext else ""  # Limit text length
                }
                self.results.append(post_data)
                
            sleep(INTERVAL_DELAY)
        
        except Exception as e:
            error_message = f"Reddit search failed: {str(e)}"
            print(error_message)
            return json.dumps([{"error": error_message}])

        self.last_invoke = time()
        
        # Cache the results if successful
        if self.results:
            self._cache_results(cache_key, self.results)
            # print(f"Found {len(self.results)} posts in r/{subreddit}")
        
        else:
            # print(f"No posts found in r/{subreddit} for query: {query}")
            pass

        return json.dumps(self.results)


# Alternative version if you want to keep multiple subreddits support
class RedditSearchMultiple(BaseTool):
    name: str = 'reddit_search_multiple'
    description: str = 'Search for relevant reddit posts in multiple subreddits simultaneously'
    
    class RedditSearchMultipleInput(BaseModel):
        query: str = Field(description='Search query consisting of up to 8 relevant keywords')
        subreddits: str = Field(
            description=f'Comma-separated list of subreddits. Available: {", ".join(ALLOWED_SUBREDDITS)}', 
            default='cancer'
        )
        max_records: int = Field(description='Maximum number of posts per subreddit (max 10)', default=5)
        sort_by: str = Field(description=f'Sorting method: {", ".join(SORT_TYPES)}', default='relevance')

        @field_validator('max_records')
        @classmethod
        def max_records_must_be_in_range(cls, v):
            return min(max(1, v), 10)

        @field_validator('subreddits')
        @classmethod
        def validate_subreddits(cls, v):
            subreddit_list = [s.strip() for s in v.split(',')]
            for sr in subreddit_list:
                if sr not in ALLOWED_SUBREDDITS:
                    raise ValueError(f'Subreddit "{sr}" not in allowed list: {ALLOWED_SUBREDDITS}')
            return v
        
        @field_validator('sort_by')
        @classmethod
        def sort_by_must_be_valid(cls, v):
            if v not in SORT_TYPES:
                raise ValueError(f'sort_by must be one of {SORT_TYPES}')
            return v
    
    args_schema: type[BaseModel] = RedditSearchMultipleInput
    _cache: dict = {}
    last_invoke: float = 0

    def _run(self, query: str, subreddits: str = 'cancer', max_records: int = 5, sort_by: str = 'relevance') -> str:
        subreddit_list = [s.strip() for s in subreddits.split(',')]
        all_results = []
        
        current_time = time()
        if (current_time - self.last_invoke) < INVOKE_DELAY:
            sleep(INVOKE_DELAY - (current_time - self.last_invoke))

        try:
            for subreddit in subreddit_list:
                print(f"Searching in r/{subreddit} for '{query}'...")
                subreddit_obj = reddit_client.subreddit(subreddit)
                
                for post in subreddit_obj.search(query, sort=sort_by, limit=max_records):
                    post_data = {
                        "subreddit": subreddit,
                        "title": post.title,
                        "score": post.score,
                        "url": post.url,
                        "num_comments": post.num_comments,
                        "created_utc": post.created_utc,
                        "selftext": post.selftext[:500] if post.selftext else ""
                    }
                    all_results.append(post_data)
                    
                sleep(INTERVAL_DELAY)
                
        except Exception as e:
            error_message = f"Reddit search failed: {str(e)}"
            return json.dumps([{"error": error_message}])

        self.last_invoke = time()
        print(f"Found {len(all_results)} total posts across {len(subreddit_list)} subreddits")
        
        return json.dumps(all_results)


def reddit_search_simple(query:str, max_records=5) -> List[dict]:
    all_results = []    

    try:
        for subreddit in ['cancer', 'AskScience', 'AskDocs']:
            subreddit_obj = reddit_client.subreddit(subreddit)

            for post in subreddit_obj.search(query=query, sort='relevance', limit=max_records):
                post_data = {
                        "subreddit": subreddit,
                        "title": post.title,
                        "score": post.score,
                        "url": post.url,
                        "num_comments": post.num_comments,
                        "created_utc": post.created_utc,
                        "selftext": post.selftext[:500] if post.selftext else ""  # Limit text length
                    }
                
                all_results.append(post_data)
            
            sleep(0.5)

        return all_results
    
    except Exception as e:
        return [{
            "Reddit Search Results": f"Error {e} - Failed to fetch results from Reddit."
        }]




if __name__ == '__main__':
    print(reddit_search_simple('lung cancer diagnosis'))
    # # Test the RedditSearch tool
    # search_tool = RedditSearch()
    
    # print("=== Testing Single Subreddit Reddit Search ===")
    
    # # Test Case 1: Basic search
    # print("\n--- Test Case 1: Basic Search ---")
    # result1 = search_tool._run(
    #     query="lung cancer treatment",
    #     subreddit="cancer",
    #     max_records=3,
    #     sort_by="top"
    # )
    
    # try:
    #     parsed_result1 = json.loads(result1)
    #     print(f"Found {len(parsed_result1)} posts")
    #     if parsed_result1 and not parsed_result1[0].get('error'):
    #         print(f"First post title: {parsed_result1[0]['title'][:100]}...")
    
    # except json.JSONDecodeError:
    #     print("Failed to parse JSON result")

    # # Test Case 2: Different subreddit
    # print("\n--- Test Case 2: Medical Research Subreddit ---")
    # result2 = search_tool._run(
    #     query="immunotherapy",
    #     subreddit="medicalresearch",
    #     max_records=2,
    #     sort_by="relevance"
    # )
    
    # try:
    #     parsed_result2 = json.loads(result2)
    #     print(f"Found {len(parsed_result2)} posts")
    #     if parsed_result2 and not parsed_result2[0].get('error'):
    #         for i, post in enumerate(parsed_result2):
    #             print(f"Post {i+1}: {post['title'][:80]}...")
    # except json.JSONDecodeError:
    #     print("Failed to parse JSON result")
    
    # print("-" * 50)
    
    # # Test the multiple subreddits version
    # print("\n=== Testing Multiple Subreddits Version ===")
    # multi_search = RedditSearchMultiple()
    
    # result3 = multi_search._run(
    #     query="cancer research",
    #     subreddits="cancer,medicalresearch",
    #     max_records=2,
    #     sort_by="hot"
    # )
    
    # try:
    #     parsed_result3 = json.loads(result3)
    #     print(f"Found {len(parsed_result3)} posts across multiple subreddits")
    #     subreddit_counts = {}
    #     for post in parsed_result3:
    #         if not post.get('error'):
    #             sr = post['subreddit']
    #             subreddit_counts[sr] = subreddit_counts.get(sr, 0) + 1
        
    #     print("Posts per subreddit:", subreddit_counts)
    
    # except json.JSONDecodeError:
    #     print("Failed to parse JSON result")