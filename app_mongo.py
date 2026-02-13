from fastapi import FastAPI
from pymongo import MongoClient, ReturnDocument

app = FastAPI()

client = MongoClient(
    "mongodb://localhost:27017",
    maxPoolSize=200,          # важливо для 10 потоків/клієнтів
    connectTimeoutMS=3000,
    serverSelectionTimeoutMS=3000,
)
db = client["webcounter"]
counters = db["counters"]

@app.on_event("startup")
def init_counter():
    counters.update_one(
        {"_id": "main"},
        {"$setOnInsert": {"value": 0}},
        upsert=True
    )

@app.get("/inc")
def inc():
    doc = counters.find_one_and_update(
        {"_id": "main"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return {"count": int(doc["value"])}

@app.get("/count")
def count():
    doc = counters.find_one({"_id": "main"}, {"value": 1})
    return {"count": int(doc["value"]) if doc else 0}
