class GameError(Exception):
    """Ожидаемая игровая ошибка → HTTP 400 с кодом для клиента."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
