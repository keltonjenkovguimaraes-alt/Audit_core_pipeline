"""
MetricRegistry: central place where all MetricValues/Proportions from an
AuditInput get indexed by their conceptual name, so consistency checks can
find every place a given quantity was reported and compare them.
"""

from collections import defaultdict


class MetricRegistry:
    def __init__(self, audit_input):
        self.audit_input = audit_input
        self._by_label = defaultdict(list)
        self._index()

    def _index(self):
        for m in self.audit_input.metrics:
            self._by_label[self._normalize(m.label)].append(m)
        for p in self.audit_input.proportions:
            self._by_label[self._normalize(p.label)].append(p)

    @staticmethod
    def _normalize(label):
        return label.strip().lower()

    def occurrences(self, label):
        return self._by_label.get(self._normalize(label), [])

    def all_labels(self):
        return list(self._by_label.keys())

    def groups(self):
        """Return dict of group -> list[MetricValue] for arithmetic checks."""
        out = defaultdict(list)
        for m in self.audit_input.metrics:
            if m.group:
                out[m.group].append(m)
        return out
