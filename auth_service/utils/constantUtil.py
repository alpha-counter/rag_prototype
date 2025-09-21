import os

from dotenv import load_dotenv


ALGORITHM = "HS256"


load_dotenv()


def _require_env(key: str) -> str:
    """Fetch a required environment variable or raise a helpful error."""

    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable '{key}'."
            " Set it in your environment or .env file before starting the service."
        )
    return value


SECRET_KEY = _require_env("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
