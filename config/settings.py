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

    # Collections Names - Datos planos
    CONCEPTOS_COLLECTION: str = "conceptos"
    DESCOMPOSICIONES_COLLECTION: str = "descomposiciones"
    MEDICIONES_COLLECTION: str = "mediciones"
    TEXTOS_COLLECTION: str = "textos"
    METADATA_COLLECTION: str = "metadata"

    # Collections Names - Estructura de árbol
    ARBOL_COLLECTION: str = "arbol_conceptos"
    NODOS_COLLECTION: str = "nodos_arbol"
    RELACIONES_COLLECTION: str = "relaciones_jerarquicas"

    # Asyncronous Settings -> configuración del batch
    BATCH_SIZE: int = 100
    MAX_RETIES: int = 3

    # Tree Construction Settings -> configuración construcción de árbol
    DETECTAR_JERARQUIA_AUTOMATICA: bool = True
    VALIDAR_ARBOL_AUTOMATICO: bool = True
    CALCULAR_IMPORTES_ARBOL: bool = True

    # Niveles máximos permitidos en el árbol
    MAX_NIVELES_ARBOL: int = 10

    # Tipos de concepto para detección automática de jerarquía
    TIPOS_CAPITULO: list = ['0', '1']  # Capítulos y subcapítulos
    TIPOS_PARTIDA: list = ['2', '3']   # Partidas y subpartidas
    TIPOS_MATERIAL: list = ['4', '5']  # Materiales y mano de obra

    @classmethod
    def get_mongo_uri(cls) -> str:
        return cls.MONGO_URI

    @classmethod
    def get_database_name(cls) -> str:
        return cls.MONGO_DATABASE

    @classmethod
    def get_collections_arbol(cls) -> dict:
        """Obtiene todas las colecciones relacionadas con el árbol"""
        return {
            'arbol': cls.ARBOL_COLLECTION,
            'nodos': cls.NODOS_COLLECTION,
            'relaciones': cls.RELACIONES_COLLECTION
        }

    @classmethod
    def get_collections_datos_planos(cls) -> dict:
        """Obtiene todas las colecciones de datos planos"""
        return {
            'conceptos': cls.CONCEPTOS_COLLECTION,
            'descomposiciones': cls.DESCOMPOSICIONES_COLLECTION,
            'mediciones': cls.MEDICIONES_COLLECTION,
            'textos': cls.TEXTOS_COLLECTION,
            'metadata': cls.METADATA_COLLECTION
        }


settings = Settings()
