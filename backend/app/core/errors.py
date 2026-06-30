class ApplicationError(Exception):
    """Base exception for errors that can be shown to API clients."""


class InvalidZplError(ApplicationError):
    """Raised when an input does not contain usable ZPL."""


class RenderError(ApplicationError):
    """Raised when the local Node renderer cannot complete a conversion."""


class ConversionLimitError(ApplicationError):
    """Raised when a request exceeds a configured server limit."""
