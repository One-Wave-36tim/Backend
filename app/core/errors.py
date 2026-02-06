class AppError(Exception):
    """Base application error."""


class NotFoundError(AppError):
    pass
