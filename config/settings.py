from dotenv import load_dotenv

import os

load_dotenv()


class Settings:
    """Carga la configuración necesaria de la aplicación"""

    # Database Settings -> configuración de MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI")
    MONGO_DATABASE: str = os.getenv("MONGO_DATABASE")

    if (not MONGO_URI or not MONGO_DATABASE):
        raise Exception("Database settings are not set")

    # BC3 Settings
    DEFAULT_ENCODING: str = os.getenv("BC3_ENCODING", "cp1252")
    FIELD_SEPARATOR: str = "|"
    RECORD_SEPARATOR: str = "~"

    # Collections Names
    COMCEPTOS_COLLECTION: str = "conceptos"
    DESCOMPOSICIONES_COLLECTION: str = "descomposiciones"
    MEDICIONES_COLLECTION: str = "medicioles"
    TEXTOS_COLLECTION: str = "textos"
    METADATA_COLLECTION: str = "metadata"

    # Asyncronous Settings -> configuración del batch
    BATCH_SIZE: int = 100
    MAX_RETIES: int = 3

    @classmethod
    def get_mongo_uri(cls) -> str:
        return cls.MONGO_URI

    @classmethod
    def get_database_name(cls) -> str:
        return cls.MONGO_DATABASE


settings = Settings()
