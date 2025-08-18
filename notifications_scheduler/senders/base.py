# notifications_scheduler/senders/base.py
from abc import ABC, abstractmethod
from typing import Optional

from attr import dataclass

from notifications_scheduler.models import ResponseCode

@dataclass
class MessageSendResult:
    success: bool
    error_code: Optional[ResponseCode] = None
    message: Optional[str] = None
    
class SocialNetworkSenderInterface(ABC):
    """Contrato para enviar mensajes a través de una red social o canal."""

    @abstractmethod
    def send_message(self, client, message) -> MessageSendResult:
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

