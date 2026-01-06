"""CLI для вимірювання продуктивності оновлення лічильника у PostgreSQL.

Сценарії відповідають лабораторним завданням: lost-update, serializable,
"in-place" оновлення, блокування рядка та оптимістичний контроль конкурентності.
"""

import argparse
import threading
import time
from typing import Callable, Dict

import psycopg2
from psycopg2 import sql
from psycopg2 import extensions
from psycopg2.errors import SerializationFailure


def create_connection(dsn: str, isolation_level: int | None = None) -> extensions.connection:
    conn = psycopg2.connect(dsn)
    if isolation_level is not None:
        conn.set_isolation_level(isolation_level)
    return conn


def prepare_schema(conn: extensions.connection, user_id: int) -> None:
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
                (user_id,),
            )


def reset_counter(conn: extensions.connection, user_id: int) -> None:
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE user_counter SET counter = 0, version = 0 WHERE user_id = %s",
                (user_id,),
            )


def lost_update_worker(conn: extensions.connection, user_id: int, iterations: int) -> None:
    with conn:
        with conn.cursor() as cur:
            for _ in range(iterations):
                cur.execute("SELECT counter FROM user_counter WHERE user_id = %s", (user_id,))
                value = cur.fetchone()[0]
                value += 1
                cur.execute(
                    "UPDATE user_counter SET counter = %s WHERE user_id = %s",
                    (value, user_id),
                )
                conn.commit()


def serializable_worker(conn: extensions.connection, user_id: int, iterations: int) -> None:
    for _ in range(iterations):
        while True:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT counter FROM user_counter WHERE user_id = %s", (user_id,))
                        value = cur.fetchone()[0] + 1
                        cur.execute(
                            "UPDATE user_counter SET counter = %s WHERE user_id = %s",
                            (value, user_id),
                        )
                break
            except SerializationFailure:
                conn.rollback()
                continue


def inplace_worker(conn: extensions.connection, user_id: int, iterations: int) -> None:
    with conn:
        with conn.cursor() as cur:
            for _ in range(iterations):
                cur.execute(
                    "UPDATE user_counter SET counter = counter + 1 WHERE user_id = %s",
                    (user_id,),
                )
                conn.commit()


def row_locking_worker(conn: extensions.connection, user_id: int, iterations: int) -> None:
    with conn:
        with conn.cursor() as cur:
            for _ in range(iterations):
                cur.execute(
                    "SELECT counter FROM user_counter WHERE user_id = %s FOR UPDATE",
                    (user_id,),
                )
                value = cur.fetchone()[0] + 1
                cur.execute(
                    "UPDATE user_counter SET counter = %s WHERE user_id = %s",
                    (value, user_id),
                )
                conn.commit()


def optimistic_worker(conn: extensions.connection, user_id: int, iterations: int) -> None:
    with conn:
        with conn.cursor() as cur:
            for _ in range(iterations):
                while True:
                    cur.execute(
                        "SELECT counter, version FROM user_counter WHERE user_id = %s",
                        (user_id,),
                    )
                    counter, version = cur.fetchone()
                    counter += 1
                    cur.execute(
                        sql.SQL(
                            """
                            UPDATE user_counter
                            SET counter = %s, version = %s
                            WHERE user_id = %s AND version = %s
                            """
                        ),
                        (counter, version + 1, user_id, version),
                    )
                    if cur.rowcount:
                        conn.commit()
                        break
                    conn.rollback()


def run_scenario(
    name: str,
    dsn: str,
    clients: int,
    iterations: int,
    user_id: int,
) -> float:
    factories: Dict[str, Callable[[extensions.connection, int, int], None]] = {
        "lost-update": lost_update_worker,
        "serializable": serializable_worker,
        "in-place": inplace_worker,
        "row-locking": row_locking_worker,
        "optimistic": optimistic_worker,
    }
    if name not in factories:
        raise ValueError(f"Unknown scenario: {name}")

    barrier = threading.Barrier(clients)
    threads: list[threading.Thread] = []

    def worker() -> None:
        isolation = None
        if name == "serializable":
            isolation = extensions.ISOLATION_LEVEL_SERIALIZABLE
        conn = create_connection(dsn, isolation)
        barrier.wait()
        factories[name](conn, user_id, iterations)
        conn.close()

    start = time.perf_counter()
    for _ in range(clients):
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
    end = time.perf_counter()
    return end - start


def fetch_counter(conn: extensions.connection, user_id: int) -> tuple[int, int]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT counter, version FROM user_counter WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Counter row missing")
        return row[0], row[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark PostgreSQL counter update strategies")
    parser.add_argument("--dsn", required=True, help="PostgreSQL DSN, e.g. postgres://user:pass@localhost/db")
    parser.add_argument("--scenario", required=True, choices=[
        "lost-update", "serializable", "in-place", "row-locking", "optimistic"
    ])
    parser.add_argument("--clients", type=int, default=10, help="Number of parallel clients")
    parser.add_argument("--requests-per-client", type=int, default=10000, help="Iterations per client")
    parser.add_argument("--user-id", type=int, default=1, help="User id for the counter")
    parser.add_argument("--reset", action="store_true", help="Reset counter before running")
    parser.add_argument("--prepare", action="store_true", help="Create table and seed counter row")

    args = parser.parse_args()

    control_conn = create_connection(args.dsn)
    try:
        if args.prepare:
            prepare_schema(control_conn, args.user_id)
        if args.reset:
            reset_counter(control_conn, args.user_id)

        elapsed = run_scenario(
            args.scenario,
            args.dsn,
            args.clients,
            args.requests_per_client,
            args.user_id,
        )
        total_requests = args.clients * args.requests_per_client
        counter, version = fetch_counter(control_conn, args.user_id)
        throughput = total_requests / elapsed if elapsed else 0
        print(
            f"scenario={args.scenario} clients={args.clients} requests_per_client={args.requests_per_client} "
            f"total_requests={total_requests} elapsed={elapsed:.3f}s throughput={throughput:.2f}rps "
            f"counter={counter} version={version}"
        )
    finally:
        control_conn.close()


if __name__ == "__main__":
    main()
