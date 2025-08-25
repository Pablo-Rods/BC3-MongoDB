from database.connection import MongoDBConnection
from database.repository import BC3Repository
from parsers.bc3_parser import BC3Parser
from utils.helpers import BC3Helpers
from config.settings import settings

from typing import Optional
from pathlib import Path

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bc3_import.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BC3Reader:

    def __init__(
        self,
        mongo_uri: str = None,
        database: str = None
    ):
        self.mongo_uri = mongo_uri or settings.MONGO_URI
        self.database = database or settings.MONGO_DATABASE
        self.connection: Optional[MongoDBConnection] = None
        self.parser = BC3Parser()

    def importar_archivo(
        self,
        filepath: str,
        exportar_json: bool = False
    ) -> bool:
        """
        Importa un archivo BC3 a MongoDB

        Args:
            filepath: Ruta al archivo BC3
            exportar_json: Si True, exporta también a JSON

        Returns:
            True si la importación fue exitosa
        """
        try:
            # Leemos el archivo
            if not Path(filepath).exists():
                logger.error(f"El archivo no existe: {filepath}")
                return False

            logger.info("Leyendo BC3...")
            datos = self.parser.parse_file(filepath)

            if not datos:
                logger.error("No se pudieron parsear los datos del archivo")
                return False

            stats = BC3Helpers.calcular_estadisticas(datos)
            logger.info(f"Estadísticas del archivo: {stats}")

            if exportar_json:
                json_path = Path(filepath).with_suffix('.json')
                BC3Helpers.exportar_a_json(datos, str(json_path))

            # Subiomos los datos a Mongo
            self.connection = MongoDBConnection(self.mongo_uri, self.database)

            if not self.connection.connect():
                logger.error("No se pudo conectar a MongoDB")
                return False

            # Creamos una serie de indices para mejorar las consultas futuras
            self.connection.create_indexes()

            # Guardar en MongoDB
            logger.info("Guardando datos en MongoDB...")
            repository = BC3Repository(self.connection)
            resultado = repository.save_all(datos)

            logger.info("Importación completada:")
            logger.info(f"  - Conceptos: {resultado['conceptos_insertados']}")
            logger.info("  - Descomposiciones:" +
                        f"{resultado['descomposiciones_insertadas']}")
            logger.info(
                f"  - Mediciones: {resultado['mediciones_insertadas']}")
            logger.info(f"  - Textos: {resultado['textos_insertados']}")

            if resultado['errores']:
                logger.warning(f"Errores encontrados: {resultado['errores']}")

            return True

        except Exception as e:
            logger.error(f"Error durante la importación: {e}", exc_info=True)
            return False

        finally:
            if self.connection:
                self.connection.disconnect()


if __name__ == '__main__':
    reader = BC3Reader()
    reader.importar_archivo('./data/prueba.bc3')
