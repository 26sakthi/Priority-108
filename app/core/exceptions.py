class PriorityCareException(Exception):
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

class ResourceNotFoundException(PriorityCareException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource_type} with ID {resource_id} was not found."
        )

class InvalidOperationException(PriorityCareException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            code="INVALID_OPERATION",
            message=message,
            details=details
        )
