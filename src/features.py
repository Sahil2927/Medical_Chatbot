from src.config import get_settings
from src.mock.schemas import QuickActionMode
from src.services.exceptions import ChatServiceError


def assert_mode_enabled(mode: QuickActionMode | None) -> None:
    if mode is None:
        return
    settings = get_settings()
    if settings.is_mode_enabled(mode):
        return
    raise ChatServiceError(
        f"The '{mode}' mode is disabled on this server.",
        status_code=503,
    )
