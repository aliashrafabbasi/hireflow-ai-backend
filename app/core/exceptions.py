class LLMRateLimitError(Exception):
    """Raised when the LLM provider hits rate limits."""

    def __init__(self, message: str = "LLM rate limit exceeded. Try again later."):
        self.message = message
        super().__init__(message)
