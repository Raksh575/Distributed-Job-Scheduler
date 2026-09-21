import re
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseFailureAnalyzer(ABC):
    """Abstract interface defining the failure analyzer contract for future LLM integration."""
    
    @abstractmethod
    def analyze_failure(self, error_message: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

class RuleBasedFailureAnalyzer(BaseFailureAnalyzer):
    """
    Intelligent Rule-Based implementation analyzing job tracebacks,
    categorizing causes, and producing suggested solutions.
    """

    def analyze_failure(self, error_message: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        err = error_message or ""
        
        # 1. Connection / Timeout exceptions
        if re.search(r"(timeout|connection|unreachable|socket|http|request)", err, re.IGNORECASE):
            return {
                "failure_summary": "Network / Outbound request failed due to connection timeout.",
                "root_cause": "The external service API endpoint took too long to respond or was offline.",
                "error_category": "Network",
                "confidence_score": 0.95,
                "suggested_fixes": [
                    "Check outbound network connectivity.",
                    "Verify target API uptime.",
                    "Increase request timeout variables."
                ],
                "retry_recommendation": True,
                "estimated_recovery": "5 minutes"
            }
            
        # 2. Key / Value / Type exceptions
        elif re.search(r"(keyerror|valueerror|typeerror|validation|invalid)", err, re.IGNORECASE):
            return {
                "failure_summary": "Validation failure due to invalid payload formatting.",
                "root_cause": "The task payload arguments did not match the expected task function schema signature.",
                "error_category": "Validation",
                "confidence_score": 0.88,
                "suggested_fixes": [
                    "Review inputs payload.",
                    "Correct type formats.",
                    "Check schema validators."
                ],
                "retry_recommendation": False,
                "estimated_recovery": "0 minutes"
            }

        # 3. Database / SQL exceptions
        elif re.search(r"(database|operationalerror|psycopg2|sqlalchemy|deadlock|pool)", err, re.IGNORECASE):
            return {
                "failure_summary": "Database transactional query lock or pool exhaustion.",
                "root_cause": "Concurrent query operations triggered database lock deadlocks, or the asyncpg connection pool is fully saturated.",
                "error_category": "Database",
                "confidence_score": 0.92,
                "suggested_fixes": [
                    "Optimize query indexes.",
                    "Increase database connection pool capacity.",
                    "Adjust job priority limits."
                ],
                "retry_recommendation": True,
                "estimated_recovery": "2 minutes"
            }

        # 4. Auth / Permissions exceptions
        elif re.search(r"(permission|unauthorized|forbidden|credentials|auth|token)", err, re.IGNORECASE):
            return {
                "failure_summary": "Authorization credentials rejection.",
                "root_cause": "Task API keys or JWT tokens have expired or do not hold sufficient RBAC access rights.",
                "error_category": "Authentication",
                "confidence_score": 0.99,
                "suggested_fixes": [
                    "Verify credential configuration keys.",
                    "Rotate active access tokens.",
                    "Double-check roles permissions."
                ],
                "retry_recommendation": False,
                "estimated_recovery": "0 minutes"
            }

        # 5. Imports / Code configurations exceptions
        elif re.search(r"(import|modulenotfound|nameerror|syntaxerror)", err, re.IGNORECASE):
            return {
                "failure_summary": "Execution runtime module resolution error.",
                "root_cause": "The worker runner is missing dependencies or target task function files in its PATH.",
                "error_category": "Internal",
                "confidence_score": 0.85,
                "suggested_fixes": [
                    "Verify Python package installations in requirements.txt.",
                    "Check file modules structures."
                ],
                "retry_recommendation": False,
                "estimated_recovery": "0 minutes"
            }

        # Fallback default analysis
        return {
            "failure_summary": "Unexpected task runner traceback exception.",
            "root_cause": "An unhandled error occurred during execution of the worker function.",
            "error_category": "Unknown",
            "confidence_score": 0.50,
            "suggested_fixes": [
                "Check active worker stderr console logs.",
                "Review execution traces."
            ],
            "retry_recommendation": True,
            "estimated_recovery": "10 minutes"
        }

# Global singleton analyzer
failure_analyzer = RuleBasedFailureAnalyzer()
