import os, json
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from dotenv import load_dotenv

import warnings
warnings.simplefilter('ignore')

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

print(os.getenv("GCP_PROJECT_ID"), os.getenv("FIRESTORE_DB"), os.getenv("FIRESTORE_COLLECTION") )

# Initialize client
db = firestore.Client(
    project=os.getenv("GCP_PROJECT_ID"),
    database=os.getenv("FIRESTORE_DB")
)

users_coll: firestore.Client.collection = db.collection(os.getenv("FIRESTORE_COLLECTION"))
print()

docs = users_coll.get()
for doc in docs:
    print(doc.id)

exit()

users_coll.document("test_userid_1").set({
    "name": "Atharva",
    "email": "atharva@example.com",
    "age": 22
})
print("Added/Updated document with custom ID: custom_user_id")


users_coll.document("test_userid_2").set({
})
print("Added empty document")


# See subcollections
docs = users_coll.get()
for doc in docs:
    print(f"User ID: {doc.id}")
    subcollections = doc.reference.collections()
    for subcoll in subcollections:
        print(f"  Sub-collection: {subcoll.id}")
        for subdoc in subcoll.stream():
            print(f"    {subdoc.id} => {subdoc.to_dict()}")