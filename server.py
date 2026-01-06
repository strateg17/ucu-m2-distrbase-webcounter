import os
import pathlib
import threading
import fcntl
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class CounterResponse(BaseModel):
    count: int


class Counter:
    def increment(self) -> int:
        raise NotImplementedError

    def get(self) -> int:
        raise NotImplementedError


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


def build_counter() -> Counter:
    storage_mode = os.getenv("STORAGE_MODE", "memory").lower()
    if storage_mode == "memory":
        return MemoryCounter()
    if storage_mode == "file":
        path = os.getenv("COUNTER_FILE", "./data/counter.txt")
        return FileCounter(path)
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
