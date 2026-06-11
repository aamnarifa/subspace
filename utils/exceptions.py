class CreditBudgetExceededError(Exception):
    """Raised when the actual or estimated credits exceed the budget."""
    pass

class ConfigurationError(Exception):
    """Raised when critical configuration checks fail on startup."""
    pass
