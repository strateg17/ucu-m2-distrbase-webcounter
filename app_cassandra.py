from fastapi import FastAPI
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

CASS_HOST = "127.0.0.1"
KEYSPACE = "webcounter"
COUNTER_ID = "main"

app = FastAPI()

cluster = Cluster([CASS_HOST])
session = cluster.connect()

@app.on_event("startup")
def startup():
    # Ensure keyspace/table exist (optional if you run CQL scripts)
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)
    session.set_keyspace(KEYSPACE)
    session.execute("""
        CREATE TABLE IF NOT EXISTS counters (
          id text PRIMARY KEY,
          value counter
        )
    """)
    # create row if missing (safe no-op)
    session.execute("UPDATE counters SET value = value + 0 WHERE id=%s", (COUNTER_ID,))

@app.on_event("shutdown")
def shutdown():
    session.shutdown()
    cluster.shutdown()

@app.get("/inc")
def inc():
    # Atomic counter increment
    session.execute("UPDATE counters SET value = value + 1 WHERE id=%s", (COUNTER_ID,))
    # Return current value (extra read; OK for lab, but costs performance)
    row = session.execute("SELECT value FROM counters WHERE id=%s", (COUNTER_ID,)).one()
    return {"count": int(row.value) if row else 0}

@app.get("/count")
def count():
    row = session.execute("SELECT value FROM counters WHERE id=%s", (COUNTER_ID,)).one()
    return {"count": int(row.value) if row else 0}
