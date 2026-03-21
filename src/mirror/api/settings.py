import os


def get_cors_origins() -> list[str]:
    configured = os.getenv(
        "MIRROR_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]
