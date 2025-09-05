from config.settings import settings

from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo import MongoClient
from typing import Optional

import logging

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Gestor de conexión con la base de datos"""

    def __init__(
        self,
        uri: str = None,
        database_name: str = None
    ):
        self.database_name = database_name or settings.get_database_name()
        self.uri = uri or settings.get_mongo_uri()
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self._connected = False

    def connect(self) -> bool:
        try:
            logger.info(f"Conectando a MongoDB: {self.uri}")

            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMs=5000,
                connectTimeoutMS=10000
            )

            self.client.admin.command('ping')

            self.database = self.client[self.database_name]
            self._connected = True

            logger.info(
                "Conectado exitosamente a la base de datos:" +
                f"{self.database_name}")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Error de conexión a MongoDB: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Error inesperado conectando a MongoDB: {e}")
            self._connected = False
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Desconectado de MongoDB")

    def get_collection(
        self,
        collection_name: str
    ) -> Optional[Collection]:
        if not self._connected:
            logger.error("No hay conexión a MongoDB")
            return None

        return self.database[collection_name]

    def _is_connected(self) -> bool:
        return self._connected

    def create_indexes(self):
        if not self._connected:
            logger.error("No hay conexión para crear índices")
            return

        try:
            # Índices para conceptos
            conceptos_col = self.get_collection(settings.CONCEPTOS_COLLECTION)
            if conceptos_col is not None:  # CORREGIDO
                conceptos_col.create_index("codigo", unique=True, sparse=True)
                conceptos_col.create_index("tipo")
                conceptos_col.create_index("archivo_origen")

            # Índices para descomposiciones
            desc_col = self.get_collection(
                settings.DESCOMPOSICIONES_COLLECTION)
            if desc_col is not None:  # CORREGIDO
                desc_col.create_index("codigo_padre")
                desc_col.create_index(
                    [("codigo_padre", 1), ("archivo_origen", 1)])

            # Índices para mediciones
            med_col = self.get_collection(settings.MEDICIONES_COLLECTION)
            if med_col is not None:  # CORREGIDO
                med_col.create_index("codigo_padre")
                med_col.create_index("codigo_hijo")
                med_col.create_index([("codigo_padre", 1), ("codigo_hijo", 1)])

            # Índices para textos
            textos_col = self.get_collection(settings.TEXTOS_COLLECTION)
            if textos_col is not None:  # CORREGIDO
                textos_col.create_index("codigo")
                textos_col.create_index([("codigo", 1), ("archivo_origen", 1)])

            logger.info("Índices creados exitosamente")

        except Exception as e:
            logger.error(f"Error creando índices: {e}")

    def __enter__(self):
        """Context manager - entrada"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - salida"""
        self.disconnect()
