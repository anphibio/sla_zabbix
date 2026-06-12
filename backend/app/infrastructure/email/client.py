from __future__ import annotations

import smtplib
from email.message import EmailMessage


class EmailDeliveryError(Exception):
    pass


class EmailClient:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        sender_email: str,
        use_tls: bool = True,
        smtp_factory=None,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender_email = sender_email
        self.use_tls = use_tls
        self._smtp_factory = smtp_factory or smtplib.SMTP

    def send_report(
        self,
        *,
        recipient_email: str,
        subject: str,
        body: str,
        attachment_name: str,
        attachment_content: bytes,
        attachment_mime_type: str,
    ) -> None:
        if not self.host or not self.sender_email:
            raise EmailDeliveryError("smtp_not_configured")

        message = EmailMessage()
        message["From"] = self.sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body)

        maintype, subtype = attachment_mime_type.split("/", 1)
        message.add_attachment(
            attachment_content,
            maintype=maintype,
            subtype=subtype,
            filename=attachment_name,
        )

        try:
            with self._smtp_factory(self.host, self.port) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.username:
                    smtp.login(self.username, self.password)
                smtp.send_message(message)
        except Exception as exc:  # noqa: BLE001
            raise EmailDeliveryError(str(exc)) from exc
