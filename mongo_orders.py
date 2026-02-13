from datetime import datetime, timezone
from pprint import pprint

from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
db = MongoClient(MONGO_URI)["shop"]

items = db.items
orders = db.orders

# --- helpers ---
def show(title, cursor_or_obj):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)
    if hasattr(cursor_or_obj, "__iter__") and not isinstance(cursor_or_obj, dict):
        for x in cursor_or_obj:
            pprint(x)
    else:
        pprint(cursor_or_obj)

def dt(s):  # "2026-02-03" or "2026-02-03T12:00:00Z"
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

# --- ensure items exist ---
if items.count_documents({}) == 0:
    raise SystemExit("ERROR: items is empty. Run items_basic.py first.")

# --- pick items by model (minimal, as in your task) ---
def get_item(model):
    doc = items.find_one({"model": model}, {"_id": 1, "price": 1, "model": 1})
    if not doc:
        raise SystemExit(f"ERROR: item not found: model='{model}'")
    return doc

iphone = get_item("iPhone 6")
tv = get_item("Bravia X90K")
watch = get_item("Apple Watch SE")
samsung = get_item("Galaxy S21")
laptop = get_item("ThinkPad X1 Carbon")

show("ITEM IDS", [
    {"model": "iPhone 6", "_id": iphone["_id"]},
    {"model": "Bravia X90K", "_id": tv["_id"]},
    {"model": "Apple Watch SE", "_id": watch["_id"]},
    {"model": "WH-1000XM5", "_id": samsung["_id"]},
    {"model": "ThinkPad X1 Carbon", "_id": laptop["_id"]},
])

# --- reset orders ---
orders.drop()

# 1) Create several orders (one item in multiple orders) + embed customer + refs for items
docs = [
    {
        "order_number": 201513,
        "date": dt("2026-02-01T10:00:00Z"),
        "items_id": [iphone["_id"], watch["_id"]],
        "total_sum": float(iphone["price"] + watch["price"]),
        "customer": {"name": "Andrii", "surname": "Rodionov", "phones": [9876543, 1234567], "address": "Peremohy 37, Kyiv, UA"},
        "payment": {"card_owner": "Andrii Rodionov", "cardId": 12345678},
    },
    {
        "order_number": 201514,
        "date": dt("2026-02-03T12:00:00Z"),
        "items_id": [iphone["_id"], tv["_id"]],  # iphone повторюється
        "total_sum": float(iphone["price"] + tv["price"]),
        "customer": {"name": "Andrii", "surname": "Rodionov", "phones": [9876543], "address": "Peremohy 37, Kyiv, UA"},
        "payment": {"card_owner": "Andrii Rodionov", "cardId": 12345678},
    },
    {
        "order_number": 201515,
        "date": dt("2026-02-05T16:30:00Z"),
        "items_id": [laptop["_id"], samsung["_id"]],
        "total_sum": float(laptop["price"] + samsung["price"]),
        "customer": {"name": "Olena", "surname": "Koval", "phones": [5550011], "address": "Khreshchatyk 1, Kyiv, UA"},
        "payment": {"card_owner": "Olena Koval", "cardId": 87654321},
    },
]
orders.insert_many(docs)
show("1) INSERTED orders (brief)", orders.find({}, {"_id": 0, "order_number": 1, "total_sum": 1, "customer": 1, "items_id": 1}).sort("order_number", 1))

# 2) Print all orders
show("2) ALL orders", orders.find({}, {"_id": 0}).sort("order_number", 1))

# 3) Orders with total_sum > threshold
threshold = 1000
show(f"3) total_sum > {threshold}", orders.find({"total_sum": {"$gt": threshold}}, {"_id": 0, "order_number": 1, "total_sum": 1}))

# 4) Orders by one customer
show("4) customer=Andrii Rodionov", orders.find({"customer.name": "Andrii", "customer.surname": "Rodionov"}, {"_id": 0, "order_number": 1, "total_sum": 1}))

# 5) Orders with a specific item (ObjectId)
show("5) orders containing iPhone (ObjectId)", orders.find({"items_id": iphone["_id"]}, {"_id": 0, "order_number": 1, "items_id": 1, "total_sum": 1}))

# 6) Add item to all orders containing a given item + inc total_sum by X
X = float(samsung["price"])
res = orders.update_many(
    {"items_id": iphone["_id"]},
    {"$addToSet": {"items_id": samsung["_id"]}, "$inc": {"total_sum": X}},
)
show("6) update_many: add samsung to iphone-orders + inc total_sum by X", {"matched": res.matched_count, "modified": res.modified_count, "X": X})

# 7) Projection customer + cardId where total_sum > some amount
proj_thr = 1200
show(f"7) projection (customer + cardId) where total_sum > {proj_thr}",
     orders.find({"total_sum": {"$gt": proj_thr}}, {"_id": 0, "order_number": 1, "customer": 1, "payment.cardId": 1}))

# 8) Remove an item from orders in date range
res2 = orders.update_many(
    {"date": {"$gte": dt("2026-02-01"), "$lt": dt("2026-02-04")}},
    {"$pull": {"items_id": watch["_id"]}},
)
show("8) pull watch in date range [2026-02-01..2026-02-04)", {"matched": res2.matched_count, "modified": res2.modified_count})

# 9) Rename surname for all orders
res3 = orders.update_many({"customer.surname": "Rodionov"}, {"$set": {"customer.surname": "Rodionovych"}})
show("9) rename surname Rodionov -> Rodionovych", {"matched": res3.matched_count, "modified": res3.modified_count})

# 10) Join-like: for one order show surname + item names/prices (lookup)
target = 201514
pipeline = [
    {"$match": {"order_number": target}},
    {"$lookup": {"from": "items", "localField": "items_id", "foreignField": "_id", "as": "items"}},
    {"$project": {"_id": 0, "order_number": 1, "customer_surname": "$customer.surname", "items.model": 1, "items.price": 1}},
]
show(f"10) lookup join-like for order_number={target}", list(orders.aggregate(pipeline)))

print("\nDONE ✅")
