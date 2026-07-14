"""
Canonical, well-established statistical formulas.

IMPORTANT: These exist ONLY as a reference to compare reported values
against. Nothing in audit_core ever overwrites a source document's
numbers with the output of these functions — checks/statistics.py uses
them purely to compute what a check believes the "correct" figure would
be, and reports both side by side as a FLAG.
"""

import math
from scipy import stats


def wilson_score_interval(k: int, n: int, confidence: float = 0.95):
    """
    Wilson score interval for a binomial proportion. Source: Wilson (1927),
    "Probable Inference, the Law of Succession, and Statistical Inference".
    Well-behaved at small n and at extreme proportions (k=0 or k=n),
    unlike the naive normal-approximation interval.
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = k / n
    denom = 1 + z**2 / n
    center = p_hat + z**2 / (2 * n)
    margin = z * math.sqrt((p_hat * (1 - p_hat) / n) + (z**2 / (4 * n**2)))
    low = (center - margin) / denom
    high = (center + margin) / denom
    return max(0.0, low), min(1.0, high)


def clopper_pearson_interval(k: int, n: int, confidence: float = 0.95):
    """
    Exact Clopper-Pearson interval for a binomial proportion, based on
    inverting the binomial test via the Beta distribution. More
    conservative than Wilson (guaranteed coverage >= nominal, no
    approximation), commonly the default when an "exact" interval is
    required.
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    alpha = 1 - confidence
    low = 0.0 if k == 0 else stats.beta.ppf(alpha / 2, k, n - k + 1)
    high = 1.0 if k == n else stats.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return low, high


def rule_of_three_bound(n: int):
    """
    Rule-of-three upper bound on the true rate, given ZERO observed events
    in n trials. Source: Hanley & Lippman-Hand (1983). Approximation is
    typically only considered valid for n >= 30; below that, prefer the
    exact Clopper-Pearson bound at k=0 instead.
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    return 3.0 / n


def is_rule_of_three_valid_n(n: int, threshold: int = 30):
    return n >= threshold


def precision(tp: int, fp: int):
    denom = tp + fp
    if denom == 0:
        return None
    return tp / denom


def recall(tp: int, fn: int):
    denom = tp + fn
    if denom == 0:
        return None
    return tp / denom


def f1_score(tp: int, fp: int, fn: int):
    p = precision(tp, fp)
    r = recall(tp, fn)
    if p is None or r is None or (p + r) == 0:
        return None
    return 2 * p * r / (p + r)


REGISTRY = {
    "wilson_score_interval": {
        "fn": wilson_score_interval,
        "source": "Wilson (1927)",
        "applies_when": "binomial proportion, any n, including k=0 or k=n",
    },
    "clopper_pearson_interval": {
        "fn": clopper_pearson_interval,
        "source": "Clopper & Pearson (1934)",
        "applies_when": "binomial proportion, exact coverage required",
    },
    "rule_of_three_bound": {
        "fn": rule_of_three_bound,
        "source": "Hanley & Lippman-Hand (1983)",
        "applies_when": "zero observed events, n >= 30",
    },
    "precision": {"fn": precision, "source": "standard", "applies_when": "TP/FP known"},
    "recall": {"fn": recall, "source": "standard", "applies_when": "TP/FN known"},
    "f1_score": {"fn": f1_score, "source": "standard", "applies_when": "TP/FP/FN known"},
}
