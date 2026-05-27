from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.value_objects.rating import Rating


@dataclass
class HiverSearchResult:
    """DTO used solely for sorting — carries the fields each strategy needs."""
    hiver_id: str
    avg_rating: float
    distance_m: float
    min_price: float
    response_rate: float
    is_boosted: bool


class SearchSortStrategy(ABC):
    """
    Strategy Pattern (SOLID O — Open/Closed):
    Open for extension (add ByPopularity, ByResponseRate),
    closed for modification (existing strategies never change).
    """

    @abstractmethod
    def sort(self, hivers: list[HiverSearchResult]) -> list[HiverSearchResult]: ...


class SortByRating(SearchSortStrategy):
    def sort(self, hivers: list[HiverSearchResult]) -> list[HiverSearchResult]:
        return sorted(hivers, key=lambda h: h.avg_rating, reverse=True)


class SortByDistance(SearchSortStrategy):
    def sort(self, hivers: list[HiverSearchResult]) -> list[HiverSearchResult]:
        return sorted(hivers, key=lambda h: h.distance_m)


class SortByPrice(SearchSortStrategy):
    def sort(self, hivers: list[HiverSearchResult]) -> list[HiverSearchResult]:
        return sorted(hivers, key=lambda h: h.min_price)


class SortByRecommended(SearchSortStrategy):
    """Weighted combination of rating, distance, response rate, and boost."""

    def sort(self, hivers: list[HiverSearchResult]) -> list[HiverSearchResult]:
        def score(h: HiverSearchResult) -> float:
            return (
                h.avg_rating * 0.4
                + (1 / max(h.distance_m, 1)) * 0.3
                + h.response_rate * 0.2
                + (0.1 if h.is_boosted else 0.0)
            )
        return sorted(hivers, key=score, reverse=True)


SORT_STRATEGIES: dict[str, SearchSortStrategy] = {
    "rating":      SortByRating(),
    "distance":    SortByDistance(),
    "price":       SortByPrice(),
    "recommended": SortByRecommended(),
}


def get_sort_strategy(name: str) -> SearchSortStrategy:
    strategy = SORT_STRATEGIES.get(name)
    if strategy is None:
        raise ValueError(f"Unknown sort strategy: {name!r}. Choose from {list(SORT_STRATEGIES)}")
    return strategy
