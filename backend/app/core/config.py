from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    app_name: str = "zabbix-sla"
    app_env: str = "dev"
    app_version: str = "0.1.0"
    smtp_host: str = getenv("SMTP_HOST", "")
    smtp_port: int = int(getenv("SMTP_PORT", "587"))
    smtp_username: str = getenv("SMTP_USERNAME", "")
    smtp_password: str = getenv("SMTP_PASSWORD", "")
    smtp_sender_email: str = getenv("SMTP_SENDER_EMAIL", "")
    smtp_use_tls: bool = getenv("SMTP_USE_TLS", "true").lower() == "true"


settings = Settings()
