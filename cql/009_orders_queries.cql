-- 009_orders_queries.cql
USE shop;

-- 1) DESCRIBE
DESCRIBE TABLE orders_by_customer;

-- 2) For customer: all orders sorted by time (DESC already by clustering order)
SELECT customer_name, order_time, order_id, total_sum, items
FROM orders_by_customer
WHERE customer_name='Andrii';

-- 3) For customer: find orders with a specific item
-- (fast via dedicated table, no ALLOW FILTERING)
SELECT customer_name, item_id, order_time, order_id, total_sum
FROM orders_by_customer_item
WHERE customer_name='Andrii' AND item_id=11111111-1111-1111-1111-111111111111;

-- 4) For customer: orders in time range
SELECT customer_name, order_time, order_id, total_sum
FROM orders_by_customer
WHERE customer_name='Andrii'
  AND order_time >= '2026-02-01 00:00:00+0000'
  AND order_time <= '2026-02-05 23:59:59+0000';

-- 4b) For customer: count orders in time range
SELECT COUNT(*)
FROM orders_by_customer
WHERE customer_name='Andrii'
  AND order_time >= '2026-02-01 00:00:00+0000'
  AND order_time <= '2026-02-05 23:59:59+0000';

-- 5) For each customer: total spent (precomputed table)
SELECT customer_name, total_spent FROM customer_order_stats;

-- 6) For each customer: max order (precomputed table)
SELECT customer_name, max_order_sum, max_order_id, max_order_time
FROM customer_order_stats;
