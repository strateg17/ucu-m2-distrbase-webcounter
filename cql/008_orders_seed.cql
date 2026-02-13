-- 008_orders_seed.cql
USE shop;

TRUNCATE orders_by_customer;
TRUNCATE orders_by_customer_item;
TRUNCATE customer_order_stats;

-- Define a few stable item ids for demo (copy/paste if you want constant values)
-- We'll just use uuid() inline in inserts, but for "search by specific item" it's convenient
-- to have at least one known item id. So we create 2 constants by manual UUID literals.
-- You can keep these as-is.
-- itemA: 11111111-1111-1111-1111-111111111111
-- itemB: 22222222-2222-2222-2222-222222222222
-- itemC: 33333333-3333-3333-3333-333333333333

-- Customer: Andrii (3 orders, with overlapping items)
INSERT INTO orders_by_customer (customer_name, order_time, order_id, total_sum, delivery_address, items)
VALUES ('Andrii', '2026-02-01 10:00:00+0000', uuid(), 1200.00, 'Kyiv, UA', {11111111-1111-1111-1111-111111111111, 22222222-2222-2222-2222-222222222222});

INSERT INTO orders_by_customer (customer_name, order_time, order_id, total_sum, delivery_address, items)
VALUES ('Andrii', '2026-02-03 12:00:00+0000', uuid(), 800.00, 'Kyiv, UA', {11111111-1111-1111-1111-111111111111});

INSERT INTO orders_by_customer (customer_name, order_time, order_id, total_sum, delivery_address, items)
VALUES ('Andrii', '2026-02-06 09:15:00+0000', uuid(), 1500.00, 'Kyiv, UA', {22222222-2222-2222-2222-222222222222, 33333333-3333-3333-3333-333333333333});

-- Mirror into orders_by_customer_item (one row per (customer,item,order))
-- For each order, insert one row per item in the order:
-- Order 1 (Andrii, 2026-02-01)
INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Andrii', 11111111-1111-1111-1111-111111111111, '2026-02-01 10:00:00+0000', uuid(), 1200.00);
INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Andrii', 22222222-2222-2222-2222-222222222222, '2026-02-01 10:00:00+0000', uuid(), 1200.00);

-- Order 2 (Andrii, 2026-02-03)
INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Andrii', 11111111-1111-1111-1111-111111111111, '2026-02-03 12:00:00+0000', uuid(), 800.00);

-- Order 3 (Andrii, 2026-02-06)
INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Andrii', 22222222-2222-2222-2222-222222222222, '2026-02-06 09:15:00+0000', uuid(), 1500.00);
INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Andrii', 33333333-3333-3333-3333-333333333333, '2026-02-06 09:15:00+0000', uuid(), 1500.00);

-- Customer: Olena (2 orders)
INSERT INTO orders_by_customer (customer_name, order_time, order_id, total_sum, delivery_address, items)
VALUES ('Olena', '2026-02-02 18:20:00+0000', uuid(), 300.00, 'Kyiv, UA', {33333333-3333-3333-3333-333333333333});

INSERT INTO orders_by_customer (customer_name, order_time, order_id, total_sum, delivery_address, items)
VALUES ('Olena', '2026-02-07 08:00:00+0000', uuid(), 2200.00, 'Kyiv, UA', {11111111-1111-1111-1111-111111111111, 33333333-3333-3333-3333-333333333333});

INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Olena', 33333333-3333-3333-3333-333333333333, '2026-02-02 18:20:00+0000', uuid(), 300.00);
INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Olena', 11111111-1111-1111-1111-111111111111, '2026-02-07 08:00:00+0000', uuid(), 2200.00);
INSERT INTO orders_by_customer_item (customer_name, item_id, order_time, order_id, total_sum)
VALUES ('Olena', 33333333-3333-3333-3333-333333333333, '2026-02-07 08:00:00+0000', uuid(), 2200.00);

-- Precomputed stats (normally your app would maintain these)
INSERT INTO customer_order_stats (customer_name, total_spent, max_order_sum, max_order_id, max_order_time, updated_at)
VALUES ('Andrii', 3500.00, 1500.00, uuid(), '2026-02-06 09:15:00+0000', '2026-02-08 00:00:00+0000');

INSERT INTO customer_order_stats (customer_name, total_spent, max_order_sum, max_order_id, max_order_time, updated_at)
VALUES ('Olena', 2500.00, 2200.00, uuid(), '2026-02-07 08:00:00+0000', '2026-02-08 00:00:00+0000');

-- Quick verify
SELECT customer_name, order_time, total_sum, items FROM orders_by_customer WHERE customer_name='Andrii';
SELECT customer_name, item_id, order_time, total_sum FROM orders_by_customer_item WHERE customer_name='Andrii' AND item_id=11111111-1111-1111-1111-111111111111;
SELECT * FROM customer_order_stats;
