"""Shared fixtures for audit_core tests."""

import pytest
from audit_core.ingest.schema import (
    AuditInput, MetricValue, Proportion, NamedDefinition,
    ValidationSet, FormulaApplication,
)
from audit_core.registry import MetricRegistry


@pytest.fixture
def empty_audit_input():
    return AuditInput(document_title="Test Document")


@pytest.fixture
def registry_for(empty_audit_input):
    """Factory: build a registry from whatever audit_input the test constructs."""
    def _make(audit_input):
        return MetricRegistry(audit_input)
    return _make
