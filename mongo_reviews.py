from datetime import datetime, timezone
from pprint import pprint

from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
db = MongoClient(MONGO_URI)["shop"]

# 1) recreate capped collection
if "reviews" in db.list_collection_names():
    db.reviews.drop()

db.create_collection(
    "reviews",
    capped=True,
    size=10_240,  # bytes; just needs to be >= docs size
    max=5         # keep only last 5 documents
)

reviews = db.reviews

print("isCapped:", reviews.options().get("capped", False))
print("options:", reviews.options())

# 2) insert 6 reviews (structure is up to us)
docs = [
    {"ts": datetime.now(timezone.utc), "user": "u1", "rating": 5, "text": "Great service"},
    {"ts": datetime.now(timezone.utc), "user": "u2", "rating": 4, "text": "Fast delivery"},
    {"ts": datetime.now(timezone.utc), "user": "u3", "rating": 3, "text": "Okay overall"},
    {"ts": datetime.now(timezone.utc), "user": "u4", "rating": 2, "text": "Late shipment"},
    {"ts": datetime.now(timezone.utc), "user": "u5", "rating": 5, "text": "Perfect"},
    {"ts": datetime.now(timezone.utc), "user": "u6", "rating": 1, "text": "Bad support"},
]
reviews.insert_many(docs)

# 3) verify: only 5 remain, oldest is removed
print("\ncountDocuments (expected 5):", reviews.count_documents({}))

print("\nAll reviews (expected u1 missing, only u2..u6 remain):")
for r in reviews.find({}, {"_id": 0, "user": 1, "rating": 1, "text": 1, "ts": 1}):
    pprint(r)

print("\nDONE ✅")
