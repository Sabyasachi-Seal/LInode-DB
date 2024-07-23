import dotenv
dotenv.load_dotenv()
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str
    stackscript_mysql: int
    stackscript_postgresql: int
    stackscript_mongodb: int
    secret_key: str
    init_email: str
    init_password: str
    linode_token: str

    class Config:
        env_file = ".env"

settings = Settings()