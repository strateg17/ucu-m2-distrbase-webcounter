-- 006_updates_items.cql
USE shop;

-- 0) Find the exact primary key (category, price, item_id)
SELECT category, price, item_id, name, producer, attrs
FROM items
WHERE category='Phone' AND name='iPhone 6';

-- 1) Copy item_id from the output and paste into the statements below.
-- Example placeholder item_id: 68dd7c2f-5cc4-4921-963d-f6413576f43d

-- 2) Update description
UPDATE items
SET description = 'Updated description for iPhone 6'
WHERE category='Phone' AND price=599.00 AND item_id=68dd7c2f-5cc4-4921-963d-f6413576f43d;

-- 3) Change existing attribute value
UPDATE items
SET attrs['storage_gb'] = '256'
WHERE category='Phone' AND price=599.00 AND item_id=68dd7c2f-5cc4-4921-963d-f6413576f43d;

-- 4) Add new attribute
UPDATE items
SET attrs['wireless_charging'] = 'true'
WHERE category='Phone' AND price=599.00 AND item_id=68dd7c2f-5cc4-4921-963d-f6413576f43d;

-- 5) Delete an attribute
DELETE attrs['nfc']
FROM items
WHERE category='Phone' AND price=599.00 AND item_id=68dd7c2f-5cc4-4921-963d-f6413576f43d;

-- 6) Verify after changes (same PK!)
SELECT category, price, item_id, name, producer, description, attrs
FROM items
WHERE category='Phone' AND price=599.00 AND item_id=68dd7c2f-5cc4-4921-963d-f6413576f43d;
