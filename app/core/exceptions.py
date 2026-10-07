class ConflictError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InvalidOrderStateError(Exception):
    pass


class InvalidPaymentStateError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass
