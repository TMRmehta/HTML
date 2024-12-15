"""
Firestore Schema:

users (collection)
  └── {userid} (document)
        └── chats (collection)
              └── {chatid} (document)
                    ├── metadata (map)
                    │     ├── title: string
                    │     ├── created_at: timestamp
                    └── messages (collection)
                          └── {messageid} (document)
                                ├── sender: "user" | "ai" | "tool"
                                ├── content: string
                                ├── reasoning: list
                                ├── sources: list
                                ├── tools: list
                                ├── timestamp: timestamp
                                └── additional_data (map, optional)
"""

import os, sys, logging
from dotenv import load_dotenv
from google.cloud import firestore
from datetime import datetime, timezone
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from CustomTools.models import ChatMessageTemplate

# Load .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


class ChatsDatabase:
    def __init__(self, debug=False):
        self.db: firestore.Client = firestore.Client(
            project=os.getenv("GCP_PROJECT_ID"),
            database=os.getenv("FIRESTORE_DB", "(default)")
        )
        self.users_coll = self.db.collection(os.getenv("FIRESTORE_COLLECTION"))
        self.debug = debug

        try:
            self.users_coll.limit(1).get()
            logging.info("✅ Successfully connected to Firestore")
        except Exception as e:
            logging.critical(f"❌ Connection failed with Firestore: {e}")

    def get_db_pointer(self):
        return self.users_coll

    def user_exists(self, user_id: str) -> bool:
        return self.users_coll.document(user_id).get().exists

    def list_all_users(self):
        for doc in self.users_coll.get():
            print(doc.id)

    def chat_exists(self, user_id: str, chat_id: str) -> bool:
        chats_coll = self.users_coll.document(user_id).collection("chats")
        return chats_coll.document(chat_id).get().exists

    def create_new_user(self, user_id: str) -> bool:
        try:
            if not self.user_exists(user_id):
                self.users_coll.document(user_id).set({"create_ts": datetime.now(timezone.utc)})
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to create new user {user_id}. Exception - {e}")
            return False

    def delete_user(self, user_id: str):
        if self.user_exists(user_id):
            self.users_coll.document(user_id).delete()
            return True
        return False

    def create_chat(self, user_id: str, chat_id: str, title: str = "Untitled Chat") -> bool:
        try:
            if not self.user_exists(user_id):
                self.create_new_user(user_id)

            chat_ref = self.users_coll.document(user_id).collection("chats").document(chat_id)
            
            if not chat_ref.get().exists:
                chat_ref.set({
                    "metadata": {
                        "title": title,
                        "created_at": datetime.now(timezone.utc)
                    }
                })
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to create new chat {chat_id} for user {user_id}. Exception - {e}")
            return False

    def _ensure_chat_exists(self, user_id: str, chat_id: str):
        if not self.chat_exists(user_id, chat_id):
            self.create_chat(user_id, chat_id)

    def add_question(self, data: ChatMessageTemplate) -> Optional[dict]:
        try:
            self._ensure_chat_exists(data.user_id, data.chat_id)
            messages_coll = self.users_coll.document(data.user_id).collection("chats").document(data.chat_id).collection("messages")
            insert_data = {
                "sender": data.sender,
                "content": data.content,
                "timestamp": datetime.now(timezone.utc),
                "additional_data": data.additional_data
            }
            messages_coll.add(insert_data)
            return insert_data
        
        except Exception as e:
            logger.error(f"Failed to add user question: {data.content}. Exception - {e}")
            return None

    def add_response(self, data: ChatMessageTemplate) -> Optional[dict]:
        try:
            self._ensure_chat_exists(data.user_id, data.chat_id)
            messages_coll = self.users_coll.document(data.user_id).collection("chats").document(data.chat_id).collection("messages")
            insert_data = {
                "sender": data.sender,
                "content": data.content,
                "reasoning": data.reasoning,
                "sources": data.sources,
                "tools": data.tools,
                "timestamp": datetime.now(timezone.utc),
                "additional_data": data.additional_data
            }
            messages_coll.add(insert_data)
            return insert_data
        
        except Exception as e:
            logger.error(f"Failed to add AI response. Exception - {e}")
            return None

    def fetch_chat(self, user_id: str, chat_id: str) -> List[dict]:
        if self.chat_exists(user_id, chat_id):
            messages_coll = self.users_coll.document(user_id).collection("chats").document(chat_id).collection("messages")
            docs = messages_coll.order_by("timestamp").stream()
            return [doc.to_dict() for doc in docs]
        
        else:
            logger.error(f'Failed to fetch chat {chat_id} for user {user_id}')
            return None

    def get_chat_ids(self, user_id: str) -> List[str]:
        if self.user_exists(user_id):
            chats_coll = self.users_coll.document(user_id).collection("chats")
            return [doc.id for doc in chats_coll.stream()]
        
        return None

    def get_chats_metadata(self, user_id: str) -> List[dict]:
        """
        Returns a list of chats for a user, each with chat ID and metadata.
        Example: [{"id": "chat1", "title": "My Chat", "created_at": <timestamp>}, ...]
        """
        if self.user_exists(user_id):
            chats_coll = self.users_coll.document(user_id).collection("chats")
            chat_docs = chats_coll.stream()
            return [{"id": doc.id, **doc.to_dict().get("metadata", {})} for doc in chat_docs]
        
        return None

    def get_title(self, user_id: str, chat_id: str) -> str:
        """
        Returns the title of a given chat.
        Returns 'Untitled chat' if chat doesn't exist or has no title.
        """
        if self.chat_exists(user_id, chat_id):
            chat_ref = self.users_coll.document(user_id).collection("chats").document(chat_id)
            metadata = chat_ref.get().to_dict().get("metadata", {})
            return metadata.get("title", "Untitled chat")
        
        else:
            logging.error(f'Failed to get chat title for user {user_id} chat {chat_id}')
            return "Untitled chat"



if __name__ == "__main__":
    from pprint import pprint

    # Test case
    test_user = "test_user_2"
    test_chat = "testchat1"

    CDB = ChatsDatabase()

    # Create user
    # if not CDB.user_exists(test_user):
    #     print("Creating user...")
    #     CDB.create_new_user(test_user)

    # Create chat
    # CDB.create_chat(test_user, test_chat, title="testchat")
    CDB.add_question(ChatMessageTemplate(
        user_id=test_user,
        chat_id=test_chat,
        sender='Human',
        content='Hi'
    ))
    exit('Quitting')

    # Add a question
    question = ChatMessageTemplate(
        user_id=test_user,
        chat_id=test_chat,
        sender="Human",
        content="Hello AI, how are you?",
        reasoning=[],
        sources=[],
        tools=[],
        additional_data=None
    )
    CDB.add_question(question)

    # Add an AI response
    response = ChatMessageTemplate(
        user_id=test_user,
        chat_id=test_chat,
        sender="AI",
        content="I am fine, thank you!",
        reasoning=["Greeting detected"],
        sources=[],
        tools=[],
        additional_data=None
    )
    CDB.add_response(response)

    # Fetch chat history
    print("\nChat History:")
    chat_history = CDB.fetch_chat(test_user, test_chat)
    pprint(chat_history)

    # List all users
    print("\nAll Users:")
    CDB.list_all_users()

    # List all chat IDs for the test user
    print("\nAll Chat IDs for user:")
    pprint(CDB.get_chat_ids(test_user))
