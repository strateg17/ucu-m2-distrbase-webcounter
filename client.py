import argparse
import threading
import time
from typing import List

import requests


def make_requests(base_url: str, requests_per_client: int) -> None:
    session = requests.Session()
    for _ in range(requests_per_client):
        response = session.get(f"{base_url}/inc", timeout=5)
        response.raise_for_status()


def run_load(base_url: str, clients: int, requests_per_client: int) -> float:
    barrier = threading.Barrier(clients)
    threads: List[threading.Thread] = []

    def worker() -> None:
        barrier.wait()
        make_requests(base_url, requests_per_client)

    start = time.perf_counter()
    for _ in range(clients):
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
    end = time.perf_counter()
    return end - start


def measure(base_url: str, clients: int, requests_per_client: int) -> None:
    elapsed = run_load(base_url, clients, requests_per_client)
    total_requests = clients * requests_per_client
    throughput = total_requests / elapsed if elapsed else 0
    count_response = requests.get(f"{base_url}/count", timeout=5)
    count_response.raise_for_status()
    count_value = count_response.json().get("count")
    print(
        f"clients={clients} requests_per_client={requests_per_client} "
        f"total_requests={total_requests} elapsed={elapsed:.3f}s "
        f"throughput={throughput:.2f}rps count={count_value}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="HTTP client for web counter")
    parser.add_argument("base_url", help="Base URL of the web counter, e.g. http://localhost:8080")
    parser.add_argument("--clients", type=int, default=1, help="Number of parallel clients")
    parser.add_argument(
        "--requests-per-client",
        type=int,
        default=10000,
        help="Number of /inc requests per client",
    )
    args = parser.parse_args()
    measure(args.base_url.rstrip("/"), args.clients, args.requests_per_client)


if __name__ == "__main__":
    main()
