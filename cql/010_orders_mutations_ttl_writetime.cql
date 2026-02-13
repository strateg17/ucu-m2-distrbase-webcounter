-- 010_orders_mutations_ttl_writetime.cql
USE shop;

-- 0) Pick a concrete order PK to modify
SELECT customer_name, order_time, order_id, total_sum, items
FROM orders_by_customer
WHERE customer_name='Andrii';

-- Copy the exact order_time + order_id from output and paste below.
-- Example placeholders:
-- order_time = '2026-02-06 09:15:00.000000+000'
-- order_id   = 026c8790-ef3c-464d-9860-2628ee48c92a

-- 1) Add items to a set + increase total_sum
UPDATE orders_by_customer
SET items = items + {33333333-3333-3333-3333-333333333333},
    total_sum = total_sum + 200.00
WHERE customer_name='Andrii'
  AND order_time='2026-02-06 09:15:00.000000+000'
  AND order_id=026c8790-ef3c-464d-9860-2628ee48c92a;

-- 2) Remove items from a set + decrease total_sum
UPDATE orders_by_customer
SET items = items - {11111111-1111-1111-1111-111111111111},
    total_sum = total_sum - 100.00
WHERE customer_name='Andrii'
  AND order_time='2026-02-06 09:15:00.000000+000'
  AND order_id=026c8790-ef3c-464d-9860-2628ee48c92a;

-- 3) Show WRITETIME for price column
-- (WRITETIME returns microseconds since epoch)
SELECT customer_name, order_time, order_id, total_sum, WRITETIME(total_sum) AS total_sum_written_at
FROM orders_by_customer
WHERE customer_name='Andrii'
  AND order_time='2026-02-06 09:15:00.000000+000'
  AND order_id=026c8790-ef3c-464d-9860-2628ee48c92a;

-- 4) Create an order with TTL (e.g., 30 seconds) - it will auto-expire
INSERT INTO orders_by_customer (customer_name, order_time, order_id, total_sum, delivery_address, items)
VALUES ('Andrii', '2026-02-10 10:00:00+0000', uuid(), 50.00, 'Kyiv, UA', {11111111-1111-1111-1111-111111111111})
USING TTL 30;

-- After insert, immediately check it exists:
SELECT customer_name, order_time, order_id, total_sum
FROM orders_by_customer
WHERE customer_name='Andrii'
  AND order_time='2026-02-10 10:00:00+0000';

-- Wait ~35s and run same SELECT again (row should disappear).
