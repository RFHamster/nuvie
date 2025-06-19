import enum

from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Environment(enum.Enum):
    ENV_DEV = 'dev'
    ENV_PROD = 'prod'
    ENV_STAGING = 'staging'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_ignore_empty=True,
        extra='ignore',
    )

    PROJECT_NAME: str = 'Nuvie Tec Challenge'

    LOG_LEVEL: str = 'INFO'

    SERVICE_NAME: str = ''

    SENTRY_DSN: str = ''

    ENV: Environment = Environment.ENV_DEV

    @computed_field
    @property
    def IS_ENV_DEV(self) -> Environment:
        return self.ENV == Environment.ENV_DEV

    @computed_field
    @property
    def IS_ENV_PROD(self) -> Environment:
        return self.ENV == Environment.ENV_PROD

    DEV_MODE: bool = False

    POSTGRES_DB: str = 'teste'
    POSTGRES_PORT: int | None = 5432
    POSTGRES_USER: str | None = 'postgres'
    POSTGRES_SERVER: str | None = 'localhost'
    POSTGRES_PASSWORD: str | None = 'i6#b1HDL&9'   ## fake pass
    POSTGRES_SCHEMA_NAME: str = 'postgres'

    @computed_field
    @property
    def DATABASE_URI_WITH_SCHEMA(self) -> str:
        return f'postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}?options=-c%20search_path%3D{self.POSTGRES_SCHEMA_NAME}'

    @computed_field
    @property
    def sqlalchemy_db_uri(self) -> str:
        return (
            f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
            f'@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    SECRET_KEY: str = ''


settings = Settings()
