import threading
from utils.logger import logger
from utils.exceptions import CreditBudgetExceededError

class CreditTracker:
    def __init__(self, limit: int):
        self.limit = limit
        self.credits_consumed = 0
        self._lock = threading.Lock()

    def consume(self, amount: int, description: str):
        with self._lock:
            if self.credits_consumed + amount > self.limit:
                msg = f"Credit budget exceeded! Consuming {amount} credits for '{description}' would bring total to {self.credits_consumed + amount}, which exceeds limit of {self.limit}."
                logger.error(msg)
                raise CreditBudgetExceededError(msg)
            self.credits_consumed += amount
            logger.info(f"Consumed {amount} credits for '{description}'. Total consumed: {self.credits_consumed}/{self.limit}")

    def get_consumed(self) -> int:
        with self._lock:
            return self.credits_consumed

# Global credit tracker instance
# Will be initialized in pipeline.py
credit_tracker = None

def init_credit_tracker(limit: int):
    global credit_tracker
    credit_tracker = CreditTracker(limit)

def get_credit_tracker() -> CreditTracker:
    global credit_tracker
    return credit_tracker
