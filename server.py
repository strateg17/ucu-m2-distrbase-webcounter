import os
import pathlib
import threading
import fcntl
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import hazelcast
import psycopg2
from psycopg2.pool import SimpleConnectionPool


class CounterResponse(BaseModel):
    count: int


class Counter:
    def increment(self) -> int:
        raise NotImplementedError

    def get(self) -> int:
        raise NotImplementedError

    def close(self) -> None:
        return None


class MemoryCounter(Counter):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._value = 0

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def get(self) -> int:
        with self._lock:
            return self._value


class FileCounter(Counter):
    def __init__(self, path: str) -> None:
        self._path = pathlib.Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("0")

    def increment(self) -> int:
        return self._update(1)

    def get(self) -> int:
        return self._update(0)

    def _update(self, delta: int) -> int:
        with self._path.open("r+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                content = f.read().strip() or "0"
                try:
                    value = int(content)
                except ValueError as exc:  # pragma: no cover - defensive guard
                    raise HTTPException(status_code=500, detail="Invalid counter state") from exc
                value += delta
                f.seek(0)
                f.truncate()
                f.write(str(value))
                f.flush()
                os.fsync(f.fileno())
                return value
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class PostgresCounter(Counter):
    def __init__(self, dsn: str, user_id: int = 1) -> None:
        self._user_id = user_id
        self._pool = SimpleConnectionPool(1, 10, dsn)
        self._ensure_table()

    def _ensure_table(self) -> None:
        conn = self._pool.getconn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS user_counter (
                            user_id INTEGER PRIMARY KEY,
                            counter INTEGER NOT NULL DEFAULT 0,
                            version INTEGER NOT NULL DEFAULT 0
                        )
                        """
                    )
                    cur.execute(
                        """
                        INSERT INTO user_counter(user_id, counter, version)
                        VALUES (%s, 0, 0)
                        ON CONFLICT (user_id) DO NOTHING
                        """,
                        (self._user_id,),
                    )
        finally:
            self._pool.putconn(conn)

    def _get_connection(self) -> psycopg2.extensions.connection:
        return self._pool.getconn()

    def increment(self) -> int:
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE user_counter SET counter = counter + 1 WHERE user_id = %s RETURNING counter",
                        (self._user_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise HTTPException(status_code=500, detail="Counter row missing")
                    return row[0]
        finally:
            self._pool.putconn(conn)

    def get(self) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT counter FROM user_counter WHERE user_id = %s", (self._user_id,))
                row = cur.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Counter row missing")
                return row[0]
        finally:
            self._pool.putconn(conn)


class HazelcastCounter(Counter):
    def __init__(self, members: list[str], cluster_name: str, counter_name: str, redo_operation: bool) -> None:
        self._client = hazelcast.HazelcastClient(
            cluster_name=cluster_name,
            network={"cluster_members": members, "redo_operation": redo_operation},
        )
        self._atomic = self._client.cp_subsystem.get_atomic_long(counter_name).blocking()

    def increment(self) -> int:
        return self._atomic.increment_and_get()

    def get(self) -> int:
        return self._atomic.get()

    def close(self) -> None:
        self._client.shutdown()


def build_counter() -> Counter:
    storage_mode = os.getenv("STORAGE_MODE", "memory").lower()
    if storage_mode == "memory":
        return MemoryCounter()
    if storage_mode == "file":
        path = os.getenv("COUNTER_FILE", "./data/counter.txt")
        return FileCounter(path)
    if storage_mode == "postgres":
        dsn = os.getenv("POSTGRES_DSN")
        if not dsn:
            raise ValueError("POSTGRES_DSN must be set for postgres storage mode")
        user_id = int(os.getenv("COUNTER_USER_ID", "1"))
        return PostgresCounter(dsn, user_id)
    if storage_mode == "hazelcast":
        members = [
            member.strip()
            for member in os.getenv("HAZELCAST_MEMBERS", "127.0.0.1:5701").split(",")
            if member.strip()
        ]
        cluster_name = os.getenv("HAZELCAST_CLUSTER_NAME", "dev")
        counter_name = os.getenv("HAZELCAST_ATOMIC_NAME", "web-counter")
        redo_operation = os.getenv("HAZELCAST_REDO_OPERATION", "false").lower() == "true"
        return HazelcastCounter(members, cluster_name, counter_name, redo_operation)
    raise ValueError(f"Unsupported STORAGE_MODE: {storage_mode}")


counter = build_counter()
app = FastAPI(title="Web Counter")


@app.get("/inc", response_model=CounterResponse)
def increment() -> CounterResponse:
    value = counter.increment()
    return CounterResponse(count=value)


@app.get("/count", response_model=CounterResponse)
def get_count() -> CounterResponse:
    value = counter.get()
    return CounterResponse(count=value)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("shutdown")
def shutdown_counter() -> None:
    counter.close()
