from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_title: str = "Orders API"
    debug: bool = False
    database_url: str = "sqlite:///orders.db"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 30

    model_config = {"env_file": ".env", "env_prefix": "APP_"}


settings = Settings()
