-- 004_seed_items.cql
USE shop;

-- Clean old test data (optional)
TRUNCATE items;

-- Insert test data
INSERT INTO items (category, price, item_id, name, producer, description, attrs)
VALUES ('Phone', 599.00, uuid(), 'iPhone 6', 'Apple', 'Old but gold',
        {'storage_gb':'64','color':'space_gray','nfc':'true'});

INSERT INTO items (category, price, item_id, name, producer, description, attrs)
VALUES ('Phone', 749.00, uuid(), 'Galaxy S21', 'Samsung', 'Android flagship',
        {'storage_gb':'128','color':'black','dual_sim':'true','nfc':'true'});

INSERT INTO items (category, price, item_id, name, producer, description, attrs)
VALUES ('Phone', 899.00, uuid(), 'Pixel 7', 'Google', 'Clean Android',
        {'storage_gb':'128','color':'snow','esim':'true'});

INSERT INTO items (category, price, item_id, name, producer, description, attrs)
VALUES ('TV', 1099.00, uuid(), 'Bravia X90K', 'Sony', '4K HDR TV',
        {'size_in':'55','panel':'LED','resolution':'4K','hdr':'true'});

INSERT INTO items (category, price, item_id, name, producer, description, attrs)
VALUES ('TV', 799.00, uuid(), 'Q60B', 'Samsung', '4K QLED',
        {'size_in':'50','panel':'QLED','resolution':'4K','hdr':'true'});

INSERT INTO items (category, price, item_id, name, producer, description, attrs)
VALUES ('SmartWatch', 279.00, uuid(), 'Apple Watch SE', 'Apple', 'Watch',
        {'case_mm':'44','gps':'true','lte':'false','water_resistance_atm':'5'});

-- Quick verify
SELECT category, price, item_id, name, producer, attrs FROM items WHERE category='Phone';
SELECT category, price, item_id, name, producer, attrs FROM items WHERE category='TV';
