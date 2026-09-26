class JobAgentError(Exception):
    """Base class for expected application errors."""


class ConfigurationError(JobAgentError):
    pass


class LLMError(JobAgentError):
    pass


class ConnectorError(JobAgentError):
    pass


class SourceUnavailableError(ConnectorError):
    pass


class RateLimitError(ConnectorError):
    pass


class AuthenticationError(ConnectorError):
    pass


class NormalizationError(JobAgentError):
    pass


class MatchingError(JobAgentError):
    pass
