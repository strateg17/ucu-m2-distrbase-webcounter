-- 001_keyspace.cql
-- Keyspace with simplest replication strategy

CREATE KEYSPACE IF NOT EXISTS shop
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE shop;

DESCRIBE KEYSPACE shop;
