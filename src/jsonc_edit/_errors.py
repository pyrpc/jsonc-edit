class JsoncEditError(Exception):
    """Base exception for jsonc_edit errors."""
    pass

class DaemonError(JsoncEditError):
    """Raised when the persistent Node daemon crashes or experiences runtime issues."""
    pass

class JsoncParseError(JsoncEditError):
    """Raised when an operation fails due to invalid JSONC syntax or execution errors."""
    pass

class RuntimeBootstrapError(DaemonError):
    """Raised when Node/NPM are missing or fail to install the underlying dependency."""
    pass
