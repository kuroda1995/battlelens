"""環境設定。

ローカル開発では DATABASE_URL を直接指定し、AWS上ではEC2のUserDataが
Secrets Manager(RDS作成時に自動生成)からDB認証情報を取得して
DATABASE_URL を組み立てた上でこのプロセスを起動する想定。
アプリ本体はSecrets Managerの存在を意識しない(起動スクリプト側の責務)。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://battlelens:battlelens@localhost:3306/battlelens"
    frontend_origin: str = "*"
    pokeapi_base_url: str = "https://pokeapi.co/api/v2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
