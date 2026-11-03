from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str

    host_email: str
    guest_email: str

    timezone: str = "Asia/Kolkata"
    default_meeting_duration: int = 30

    class Config:
        env_file = ".env"


settings = Settings()