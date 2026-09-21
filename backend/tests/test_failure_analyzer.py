import pytest
from app.services.failure_analyzer import failure_analyzer

def test_timeout_analysis():
    err = "HTTP Request Timeout Exception: Connection lost to microservice node."
    analysis = failure_analyzer.analyze_failure(err, {})
    
    assert "connection timeout" in analysis["failure_summary"]
    assert analysis["retry_recommendation"] is True
    assert analysis["estimated_recovery"] == "5 minutes"

def test_value_validation_analysis():
    err = "ValueError: Input argument 'recipient' must be a valid email string."
    analysis = failure_analyzer.analyze_failure(err, {})
    
    assert "Validation failure" in analysis["failure_summary"]
    assert analysis["retry_recommendation"] is False
    assert analysis["estimated_recovery"] == "0 minutes"

def test_database_deadlock_analysis():
    err = "psycopg2.errors.DeadlockDetected: deadlocked concurrent database transactions."
    analysis = failure_analyzer.analyze_failure(err, {})
    
    assert "Database transactional query lock" in analysis["failure_summary"]
    assert analysis["retry_recommendation"] is True
    assert analysis["estimated_recovery"] == "2 minutes"
