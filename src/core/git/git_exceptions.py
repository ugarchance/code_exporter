class GitException(Exception):
    """Temel Git exception sınıfı."""
    pass

class GitInitError(GitException):
    """Git repository başlatma hatası."""
    pass

class GitConnectionError(GitException):
    """Git bağlantı hatası."""
    pass

class GitOperationError(GitException):
    """Git operasyon hatası."""
    pass