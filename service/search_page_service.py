from typing import Callable

class SearchPageService:
    BATCH_SIZE = 8
    INITIAL_FETCH = 24
    FETCH_STEP = 24
    MAX_FETCH = 96

    def __init__(self, fetch: Callable[[str, int], list[dict]]):
        self._fetch = fetch
        self._reset("")

    # Public Methods
    def start(self, query: str) -> list[dict]:
        self._reset(query)
        self._load(self.INITIAL_FETCH)  
        return self._take_next_batch()

    def next_page(self) -> list[dict]:
        if self._unseen_count() < self.BATCH_SIZE and self._can_fetch_more():
            self._refill()
        return self._take_next_batch()

    def has_more(self) -> bool:
        return self._unseen_count() > 0 or self._can_fetch_more()

    # Private Methods
    def _reset(self, query: str):
        self._query = query
        self._cache: list[dict] = []
        self._shown = 0
        self._fetch_limit = 0
        self._exhausted = False

    def _unseen_count(self) -> int:
        return len(self._cache) - self._shown

    def _can_fetch_more(self) -> bool:
        return not self._exhausted and self._fetch_limit < self.MAX_FETCH

    def _refill(self):
        new_limit = min(self._fetch_limit + self.FETCH_STEP, self.MAX_FETCH)
        new_items = self._load(new_limit)
        if not new_items:
            self._exhausted = True

    def _load(self, limit: int) -> list[dict]:
        self._fetch_limit = limit
        known_ids = {item["id"] for item in self._cache}
        fresh = [item for item in self._fetch(self._query, limit) if item["id"] not in known_ids]
        self._cache.extend(fresh)
        return fresh

    def _take_next_batch(self) -> list[dict]:
        batch = self._cache[self._shown : self._shown + self.BATCH_SIZE]
        self._shown += len(batch)
        return batch