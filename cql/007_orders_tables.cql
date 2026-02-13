-- 007_orders_tables.cql
USE shop;

-- Main table: fast per-customer queries, ordered by time
CREATE TABLE IF NOT EXISTS orders_by_customer (
  customer_name text,
  order_time timestamp,
  order_id uuid,
  total_sum decimal,
  delivery_address text,
  items set<uuid>,
  PRIMARY KEY ((customer_name), order_time, order_id)
) WITH CLUSTERING ORDER BY (order_time DESC);

-- Helper table for fast query: for a customer find orders containing a specific item
CREATE TABLE IF NOT EXISTS orders_by_customer_item (
  customer_name text,
  item_id uuid,
  order_time timestamp,
  order_id uuid,
  total_sum decimal,
  PRIMARY KEY ((customer_name, item_id), order_time, order_id)
) WITH CLUSTERING ORDER BY (order_time DESC);

-- Aggregates (maintained by application / scripts at write time)
CREATE TABLE IF NOT EXISTS customer_order_stats (
  customer_name text,
  total_spent decimal,
  max_order_sum decimal,
  max_order_id uuid,
  max_order_time timestamp,
  updated_at timestamp,
  PRIMARY KEY ((customer_name))
);

DESCRIBE TABLE orders_by_customer;
DESCRIBE TABLE orders_by_customer_item;
DESCRIBE TABLE customer_order_stats;
