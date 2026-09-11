from .models import PriorityResult


PRIORITY_ORDER = {
    "P1": 1,
    "P2": 2,
    "P3": 3,
    "P4": 4,
}


def sort_results(results: list[PriorityResult]) -> list[PriorityResult]:
    return sorted(
        results,
        key=lambda result: (
            PRIORITY_ORDER[result.priority],
            -result.risk_score,
        ),
    )