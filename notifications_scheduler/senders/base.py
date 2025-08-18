# notifications_scheduler/senders/base.py
from abc import ABC, abstractmethod

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
