"""CLI для вимірювання інкременту лічильника у Hazelcast (Task 3)."""

from __future__ import annotations

import argparse
import threading
import time
from typing import Any, Callable

import hazelcast


def create_client(members: list[str], cluster_name: str, redo_operation: bool) -> hazelcast.HazelcastClient:
    return hazelcast.HazelcastClient(
        cluster_name=cluster_name,
        cluster_members=members,
        redo_operation=redo_operation,
    )


def _build_value(amount: int) -> dict[str, int]:
    return {"amount": amount}


def _get_amount(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, dict) and "amount" in value:
        return int(value["amount"])
    if isinstance(value, (int, float)):
        return int(value)
    return int(getattr(value, "amount", 0))


def map_no_lock_worker(distributed_map: Any, key: str, iterations: int) -> None:
    for _ in range(iterations):
        value = distributed_map.get(key)
        time.sleep(0.01)
        amount = _get_amount(value) + 1
        distributed_map.put(key, _build_value(amount))


def map_pessimistic_worker(distributed_map: Any, key: str, iterations: int) -> None:
    for _ in range(iterations):
        distributed_map.lock(key)
        try:
            value = distributed_map.get(key)
            amount = _get_amount(value) + 1
            distributed_map.put(key, _build_value(amount))
        finally:
            distributed_map.unlock(key)


def map_optimistic_worker(distributed_map: Any, key: str, iterations: int) -> None:
    for _ in range(iterations):
        while True:
            value = distributed_map.get(key)
            amount = _get_amount(value)
            if distributed_map.replace_if_same(key, value, _build_value(amount + 1)):
                break


def atomic_long_worker(atomic_long, iterations: int) -> None:
    for _ in range(iterations):
        atomic_long.increment_and_get()


def run_threads(
    clients: int,
    iterations: int,
    worker_factory: Callable[[], Callable[[], None]],
) -> float:
    barrier = threading.Barrier(clients)
    threads: list[threading.Thread] = []

    def runner() -> None:
        barrier.wait()
        worker = worker_factory()
        worker()

    start = time.perf_counter()
    for _ in range(clients):
        thread = threading.Thread(target=runner)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
    end = time.perf_counter()
    return end - start


def run_map_scenario(
    scenario: str,
    distributed_map: Any,
    key: str,
    clients: int,
    iterations: int,
) -> float:
    workers = {
        "map-no-lock": lambda: lambda: map_no_lock_worker(distributed_map, key, iterations),
        "map-pessimistic": lambda: lambda: map_pessimistic_worker(distributed_map, key, iterations),
        "map-optimistic": lambda: lambda: map_optimistic_worker(distributed_map, key, iterations),
    }
    if scenario not in workers:
        raise ValueError(f"Unknown map scenario: {scenario}")

    return run_threads(clients, iterations, workers[scenario])


def run_atomic_scenario(
    atomic_long,
    clients: int,
    iterations: int,
) -> float:
    return run_threads(
        clients,
        iterations,
        lambda: lambda: atomic_long_worker(atomic_long, iterations),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Hazelcast counter scenarios")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=["map-no-lock", "map-pessimistic", "map-optimistic", "atomic-long"],
    )
    parser.add_argument(
        "--members",
        default="127.0.0.1:5701,127.0.0.1:5702,127.0.0.1:5703",
        help="Comma-separated Hazelcast members",
    )
    parser.add_argument("--cluster-name", default="dev", help="Hazelcast cluster name")
    parser.add_argument("--redo-operation", action="store_true", help="Enable redo_operation in client config")
    parser.add_argument("--clients", type=int, default=10, help="Number of parallel threads")
    parser.add_argument("--requests-per-client", type=int, default=10000, help="Iterations per thread")
    parser.add_argument("--map-name", default="counter-map", help="Map name for map scenarios")
    parser.add_argument("--key", default="likes", help="Key name for map scenarios")
    parser.add_argument("--atomic-name", default="counter-long", help="AtomicLong name")
    parser.add_argument("--reset", action="store_true", help="Reset counter before running")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    members = [member.strip() for member in args.members.split(",") if member.strip()]

    client = create_client(members, args.cluster_name, args.redo_operation)
    try:
        if args.scenario.startswith("map"):
            distributed_map = client.get_map(args.map_name).blocking()
            if args.reset:
                distributed_map.put(args.key, _build_value(0))
            else:
                distributed_map.put_if_absent(args.key, _build_value(0))

            elapsed = run_map_scenario(
                args.scenario,
                distributed_map,
                args.key,
                args.clients,
                args.requests_per_client,
            )
            total_requests = args.clients * args.requests_per_client
            value = _get_amount(distributed_map.get(args.key))
        else:
            atomic_long = client.cp_subsystem.get_atomic_long(args.atomic_name).blocking()
            if args.reset:
                atomic_long.set(0)
            elapsed = run_atomic_scenario(
                atomic_long,
                args.clients,
                args.requests_per_client,
            )
            total_requests = args.clients * args.requests_per_client
            value = atomic_long.get()

        throughput = total_requests / elapsed if elapsed else 0.0
        print(
            f"scenario={args.scenario} clients={args.clients} requests_per_client={args.requests_per_client} "
            f"total_requests={total_requests} elapsed={elapsed:.3f}s throughput={throughput:.2f}rps "
            f"count={value}"
        )
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
