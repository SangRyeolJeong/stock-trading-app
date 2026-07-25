from app.core.config import Settings


def test_comma_separated_cors_origins(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5180",
    )

    settings = Settings()

    assert settings.cors_origins == [
        "http://localhost:5173",
        "http://localhost:5180",
    ]
