class ChatServiceError(Exception):
    """Raised when message handling fails in the service layer."""

    def __init__(self, message: str, *, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code
