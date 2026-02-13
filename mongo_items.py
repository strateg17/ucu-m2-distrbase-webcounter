from pprint import pprint
from datetime import datetime, timezone
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "shop"
COLL = "items"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
items = db[COLL]

# clean start
items.drop()
print("Dropped collection:", COLL)

# 1) Створіть декілька товарів з різним набором властивостей
items.insert_many([
    {"category": "Phone", "model": "iPhone 6", "producer": "Apple", "price": 600},
    {"category": "Phone", "model": "Galaxy S21", "producer": "Samsung", "price": 750, "dual_sim": True},
    {"category": "TV", "model": "Bravia X90K", "producer": "Sony", "price": 1100, "size_in": 55, "resolution": "4K"},
    {"category": "SmartWatch", "model": "Apple Watch SE", "producer": "Apple", "price": 279, "gps": True},
    {"category": "Laptop", "model": "ThinkPad X1 Carbon", "producer": "Lenovo", "price": 1600, "ram_gb": 16},
])

print("\n=== 1) ALL ITEMS (JSON) ===")
for doc in items.find({}):
    pprint(doc)

# 2) Підрахуйте скільки товарів у певної категорії
phones_count = items.count_documents({"category": "Phone"})
print("\n=== 2) COUNT category=Phone ===")
print(phones_count)

# 3) Підрахуйте скільки є різних категорій
categories = items.distinct("category")
print("\n=== 3) DISTINCT categories + count ===")
print(categories, "count:", len(categories))

# 4) Виведіть список всіх виробників без повторів
producers = items.distinct("producer")
print("\n=== 4) DISTINCT producers ===")
print(producers)

# 5) category AND price in range ($and)
print("\n=== 5a) $and: category=Phone AND price in [500..800] ===")
for doc in items.find({
    "$and": [
        {"category": "Phone"},
        {"price": {"$gte": 500, "$lte": 800}}
    ]
}):
    pprint(doc)

# 6) model OR model ($or)
print("\n=== 5b) $or: model is iPhone 6 OR Bravia X90K ===")
for doc in items.find({
    "$or": [
        {"model": "iPhone 6"},
        {"model": "Bravia X90K"},
    ]
}):
    pprint(doc)

# 7) producers IN list ($in)
print("\n=== 5c) $in: producer in [Apple, Sony] ===")
for doc in items.find({"producer": {"$in": ["Apple", "Sony"]}}):
    pprint(doc)

# 8) updateMany: змінити існуючі + додати нові властивості за критерієм
print("\n=== 6) updateMany: category=Phone set warranty_months=12 and updated_at, inc price by -50 ===")
res = items.update_many(
    {"category": "Phone"},
    {"$set": {"warranty_months": 12, "updated_at": datetime.now(timezone.utc)},
     "$inc": {"price": -50}}
)
print("matched:", res.matched_count, "modified:", res.modified_count)

print("\nPhones after update:")
for doc in items.find({"category": "Phone"}, {"_id": 0, "model": 1, "price": 1, "warranty_months": 1, "updated_at": 1}):
    pprint(doc)

# 9) знайдіть товари у яких є певні властивості ($exists)
print("\n=== 7) $exists: field size_in exists ===")
for doc in items.find({"size_in": {"$exists": True}}, {"_id": 0, "category": 1, "model": 1, "size_in": 1, "price": 1}):
    pprint(doc)

# 10) Для знайдених товарів збільшити їх вартість на суму
print("\n=== 8) increase price by +100 for docs where size_in exists ===")
res2 = items.update_many({"size_in": {"$exists": True}}, {"$inc": {"price": 100}})
print("matched:", res2.matched_count, "modified:", res2.modified_count)

print("\nTVs after +100:")
for doc in items.find({"category": "TV"}, {"_id": 0, "model": 1, "price": 1}):
    pprint(doc)

print("\nDONE ✅")
