# notifications_scheduler/senders/base.py
from abc import ABC, abstractmethod
from typing import Optional

from notifications_scheduler.models import ErrorCode

class SocialNetworkSenderInterface(ABC):
    """Contrato para enviar mensajes a través de una red social o canal."""

    @abstractmethod
    def send_message(self, client, message) -> dict:
        """
        Envía un mensaje al cliente.
        Debe devolver un dict con información del resultado:
        {
            "success": True/False,
            "error_type": "BLOCKED" | "INVALID_NUMBER" | None,
            "response_id": "uuid o id del proveedor"
        }
        """
        pass

@dataclass
class MessageSendResult:
    success: bool
    error_code: Optional[ErrorCode] = None
    message: Optional[str] = None