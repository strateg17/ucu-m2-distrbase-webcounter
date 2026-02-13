-- 100_counter_schema.cql
CREATE KEYSPACE IF NOT EXISTS webcounter
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE webcounter;

-- Counter table: atomic increments distributed-safe
CREATE TABLE IF NOT EXISTS counters (
  id text PRIMARY KEY,
  value counter
);

-- init row (counter rows are created on first update)
-- no INSERT for counters, use UPDATE to create/increment:
UPDATE counters SET value = value + 0 WHERE id='main';

SELECT id, value FROM counters WHERE id='main';
