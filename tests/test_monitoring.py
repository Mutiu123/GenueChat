"""Tests for src.monitoring."""

import json
import logging

from src.monitoring import JSONFormatter, log_audit_event, setup_logging


class TestJSONFormatter:
    def test_produces_valid_json(self):
        fmt = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "hello"
        assert parsed["level"] == "INFO"

    def test_includes_request_id_when_present(self):
        fmt = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="msg",
            args=(),
            exc_info=None,
        )
        record.request_id = "abc-123"  # type: ignore[attr-defined]
        parsed = json.loads(fmt.format(record))
        assert parsed["request_id"] == "abc-123"


class TestSetupLogging:
    def test_does_not_raise(self):
        setup_logging()


class TestAuditLog:
    def test_log_audit_event_no_error(self):
        log_audit_event("test_event", request_id="r1", user="u1")
