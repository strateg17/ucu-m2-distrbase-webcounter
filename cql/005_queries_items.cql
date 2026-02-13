-- 005_queries_items.cql
USE shop;

-- 1) Show structure
DESCRIBE TABLE items;

-- 2) All items in category sorted by price
SELECT category, price, item_id, name, producer
FROM items
WHERE category='Phone'
ORDER BY price ASC;

-- 3) Within category: by name
SELECT category, price, item_id, name, producer, attrs
FROM items
WHERE category='Phone' AND name='iPhone 6';

-- 4) Within category: price range
SELECT category, price, item_id, name, producer
FROM items
WHERE category='Phone' AND price >= 600 AND price <= 900;

-- 5) Within category: price range + producer
SELECT category, price, item_id, name, producer
FROM items
WHERE category='Phone' AND price >= 500 AND price <= 900 AND producer='Apple';

-- 6) By presence of attribute (key exists)
SELECT category, price, item_id, name, producer, attrs
FROM items
WHERE category='Phone' AND attrs CONTAINS KEY 'nfc';

-- 7) By attribute and its value
SELECT category, price, item_id, name, producer, attrs
FROM items
WHERE category='Phone' AND attrs['storage_gb'] = '128';
