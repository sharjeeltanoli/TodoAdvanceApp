from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    BETTER_AUTH_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"
    DEBUG: bool = False
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    MCP_SERVER_URL: str = "http://localhost:8001/mcp"
    MCP_SERVER_PORT: int = 8001

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def async_database_url(self) -> str:
        """Ensure URL uses asyncpg driver with compatible params."""
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Strip params incompatible with asyncpg (sslmode, channel_binding)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params.pop("sslmode", None)
        params.pop("channel_binding", None)
        clean_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=clean_query))

    model_config = {"env_file": ".env"}


settings = Settings()
