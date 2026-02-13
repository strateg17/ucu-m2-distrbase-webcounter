-- 002_tables.cql
USE shop;

-- Items: category must be partition key, and we need ordering by price within category
CREATE TABLE IF NOT EXISTS items (
  category text,
  price decimal,
  item_id uuid,
  name text,
  producer text,
  description text,
  attrs map<text,text>,
  PRIMARY KEY ((category), price, item_id)
) WITH CLUSTERING ORDER BY (price ASC);

-- Orders: created for later parts (minimal reasonable model)
CREATE TABLE IF NOT EXISTS orders (
  customer_id uuid,
  order_time timestamp,
  order_id uuid,
  total_sum decimal,
  delivery_address text,
  items list<uuid>,
  PRIMARY KEY ((customer_id), order_time, order_id)
) WITH CLUSTERING ORDER BY (order_time DESC);

DESCRIBE TABLE items;
DESCRIBE TABLE orders;
