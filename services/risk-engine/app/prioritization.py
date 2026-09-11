from .models import PriorityResult, QueueItem
from .scoring import (
    DECISION_CATEGORY_IMMEDIATE_ACTION,
    DECISION_CATEGORY_VALIDATE_EVIDENCE,
    DECISION_CATEGORY_REMEDIATE,
    DECISION_CATEGORY_DEFER,
)


PRIORITY_ORDER = {
    "P1": 1,
    "P2": 2,
    "P3": 3,
    "P4": 4,
}

# Operational importance order for the analyst action queue.
ACTION_QUEUE_ORDER = {
    DECISION_CATEGORY_IMMEDIATE_ACTION: 1,
    DECISION_CATEGORY_VALIDATE_EVIDENCE: 2,
    DECISION_CATEGORY_REMEDIATE: 3,
    DECISION_CATEGORY_DEFER: 4,
}


def sort_results(results: list[PriorityResult]) -> list[PriorityResult]:
    return sorted(
        results,
        key=lambda result: (
            PRIORITY_ORDER[result.priority],
            -result.risk_score,
        ),
    )


def sort_results_for_queue(items: list[QueueItem]) -> list[QueueItem]:
    """Sort queue items by operational importance: action category first, then
    descending risk score within each category."""
    return sorted(
        items,
        key=lambda item: (
            ACTION_QUEUE_ORDER[item.decision_category],
            -item.risk_score,
        ),
    )