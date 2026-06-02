from threading import Lock


class InMemoryMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, int] = {}

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counters)


metrics = InMemoryMetrics()

