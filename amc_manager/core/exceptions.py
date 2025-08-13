"""Custom exception classes for AMC Manager"""


class AMCManagerError(Exception):
    """Base exception for AMC Manager"""
    pass


class AuthenticationError(AMCManagerError):
    """Authentication related errors"""
    pass


class TokenRefreshError(AuthenticationError):
    """Token refresh failures"""
    pass


class APIError(AMCManagerError):
    """Amazon Advertising API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(APIError):
    """Rate limit exceeded error"""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class AMCQueryError(AMCManagerError):
    """AMC SQL query related errors"""
    pass


class WorkflowError(AMCManagerError):
    """Workflow execution errors"""
    pass


class ValidationError(AMCManagerError):
    """Data validation errors"""
    pass


class DatabaseError(AMCManagerError):
    """Database operation errors"""
    pass