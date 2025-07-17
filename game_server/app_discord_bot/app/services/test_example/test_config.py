from .presentation_handlers.test_display_message import TestDisplayToggleMessageHandler
from .logic_handlers.test_toggle_state import TestToggleStateHandler


LOGIC_HANDLER_MAP = {
    "toggle_state": TestToggleStateHandler,
}

PRESENTATION_HANDLER_MAP = {
    "toggle_message": TestDisplayToggleMessageHandler,
}