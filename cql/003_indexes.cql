-- 003_indexes.cql
USE shop;

-- SAI indexes on scalar columns
CREATE CUSTOM INDEX IF NOT EXISTS items_name_sai
ON shop.items (name) USING 'StorageAttachedIndex';

CREATE CUSTOM INDEX IF NOT EXISTS items_producer_sai
ON shop.items (producer) USING 'StorageAttachedIndex';

-- SAI indexes on map keys / entries
CREATE CUSTOM INDEX IF NOT EXISTS items_attrs_keys_sai
ON shop.items (KEYS(attrs)) USING 'StorageAttachedIndex';

CREATE CUSTOM INDEX IF NOT EXISTS items_attrs_entries_sai
ON shop.items (ENTRIES(attrs)) USING 'StorageAttachedIndex';

DESCRIBE INDEX items_name_sai;
DESCRIBE INDEX items_producer_sai;
DESCRIBE INDEX items_attrs_keys_sai;
DESCRIBE INDEX items_attrs_entries_sai;
