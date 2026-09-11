from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI StroiApp Manager"
    api_prefix: str = "/api"
    opencart_api_url: str = ""
    opencart_api_token: str = ""
    opencart_sync_url: str = ""
    opencart_sync_token: str = ""
    deepseek_api_key: str = ""
    yandex_direct_token: str = ""
    yandex_direct_sandbox: bool = False
    yandex_webmaster_token: str = ""
    yandex_metrika_token: str = ""
    dadata_token: str = ""
    telegram_bot_token: str = ""
    manager_telegram_chat_id: str = ""
    max_bot_token: str = ""
    max_chat_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "StroiApp.ru"
    smtp_from_email: str = ""
    tenderguru_api_code: str = ""
    damia_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
