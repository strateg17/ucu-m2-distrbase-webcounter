import argparse
import threading
import time
from typing import List

from neo4j import GraphDatabase


def inc_likes(driver, item_id: str, n: int) -> None:
    # One session per thread is a good practice
    with driver.session(database="neo4j") as session:
        for _ in range(n):
            session.execute_write(
                lambda tx: tx.run(
                    """
                    MATCH (i:Item {id:$id})
                    SET i.likes = coalesce(i.likes, 0) + 1
                    """,
                    id=item_id,
                ).consume()
            )


def get_likes(driver, item_id: str) -> int:
    with driver.session(database="neo4j") as session:
        rec = session.run(
            "MATCH (i:Item {id:$id}) RETURN coalesce(i.likes,0) AS likes",
            id=item_id
        ).single()
        return int(rec["likes"]) if rec else 0


def set_likes(driver, item_id: str, value: int) -> None:
    with driver.session(database="neo4j") as session:
        session.execute_write(
            lambda tx: tx.run(
                "MATCH (i:Item {id:$id}) SET i.likes = $v",
                id=item_id,
                v=value
            ).consume()
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uri", default="bolt://localhost:7687")
    p.add_argument("--user", default="neo4j")
    p.add_argument("--password", default="test12345")
    p.add_argument("--item-id", default="I1")
    p.add_argument("--clients", type=int, default=10)
    p.add_argument("--per-client", type=int, default=10_000)
    args = p.parse_args()

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))

    # reset likes for clean run
    set_likes(driver, args.item_id, 0)

    barrier = threading.Barrier(args.clients)
    threads: List[threading.Thread] = []

    def worker():
        barrier.wait()
        inc_likes(driver, args.item_id, args.per_client)

    start = time.perf_counter()
    for _ in range(args.clients):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    end = time.perf_counter()

    total = args.clients * args.per_client
    elapsed = end - start
    likes = get_likes(driver, args.item_id)

    print(
        f"clients={args.clients} per_client={args.per_client} total={total} "
        f"elapsed={elapsed:.3f}s throughput={total/elapsed:.2f} ops/s "
        f"final_likes={likes}"
    )

    # strict correctness check
    if likes != total:
        raise SystemExit(f"ERROR: lost updates! expected {total}, got {likes}")

    driver.close()


if __name__ == "__main__":
    main()
