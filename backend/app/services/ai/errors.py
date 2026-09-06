from app.exceptions import AppError


class LlmUnavailableError(AppError):
    def __init__(self, message: str = "LLM is not configured or unreachable", details: object = None):
        super().__init__("llm_unavailable", message, 503, details)


class LlmResponseError(AppError):
    def __init__(self, message: str, details: object = None):
        super().__init__("llm_response_invalid", message, 422, details)
