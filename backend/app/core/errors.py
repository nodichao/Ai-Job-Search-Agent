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


class PersistenceError(JobAgentError):
    pass


class ShortlistError(JobAgentError):
    pass


class ShortlistIdentityError(ShortlistError):
    pass


class ShortlistDuplicateError(ShortlistError):
    pass


class ShortlistPersistenceError(ShortlistError, PersistenceError):
    pass
