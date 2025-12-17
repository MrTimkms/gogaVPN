from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite:///./vpn_billing.db"
    bot_token: str
    admin_telegram_ids: str = ""
    telegram_bot_name: str = ""
    secret_key: str = "change-me-in-production"
    debug: bool = True
    default_subscription_price: float = 100.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Преобразует строку ID админов в список"""
        if not self.admin_telegram_ids:
            return []
        return [int(id.strip()) for id in self.admin_telegram_ids.split(",") if id.strip()]


settings = Settings()

