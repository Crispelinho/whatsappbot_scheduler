# notifications_scheduler/senders/base.py
from abc import ABC, abstractmethod
from typing import Optional

from attr import dataclass

from notifications_scheduler.models import ErrorCode

@dataclass
class MessageSendResult:
    success: bool
    error_code: Optional[ErrorCode] = None
    message: Optional[str] = None
    
class SocialNetworkSenderInterface(ABC):
    """Contrato para enviar mensajes a través de una red social o canal."""

    @abstractmethod
    def send_message(
        self,
        area_code: str,
        phone_number: str,
        message: str = None,
        image_path: str = None,
        video_path: str = None
    ) -> MessageSendResult:
        """
        Envía un mensaje al cliente.
        Debe devolver un MessageSendResult con información del resultado:
        {
            "success": True/False,
            "error_code": "BLOCKED" | "INVALID_NUMBER" | None,
            "message": "Mensaje enviado con éxito" | "Error al enviar el mensaje"
        }
        """
        pass

