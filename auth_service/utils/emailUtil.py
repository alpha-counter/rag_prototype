import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema


load_dotenv()

_CONF: Optional[ConnectionConfig] = None


def _require_mail_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Missing required mail environment variable '{key}'."
            " Configure your SMTP credentials before sending email."
        )
    return value


def _get_config() -> ConnectionConfig:
    global _CONF

    if _CONF is None:
        _CONF = ConnectionConfig(
            MAIL_USERNAME=_require_mail_env("MAIL_USERNAME"),
            MAIL_PASSWORD=_require_mail_env("MAIL_PASSWORD"),
            MAIL_FROM=_require_mail_env("MAIL_FROM"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
            MAIL_SERVER=_require_mail_env("MAIL_SERVER"),
            MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "true").lower() == "true",
            MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "false").lower() == "true",
            USE_CREDENTIALS=os.getenv("MAIL_USE_CREDENTIALS", "true").lower() == "true",
            VALIDATE_CERTS=os.getenv("MAIL_VALIDATE_CERTS", "true").lower() == "true",
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
        )

    return _CONF


def send_email(subject: str, recipient: List[str], message: str):
    message = MessageSchema(
        subject=subject,
        recipients=recipient,
        body=message,
        subtype="html"
    )
    fm = FastMail(_get_config())
    return fm.send_message(message)
