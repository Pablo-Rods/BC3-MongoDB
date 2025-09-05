from database.connection import MongoDBConnection
from database.repository_arbol import BC3ArbolRepository
from parsers.arbol_constructor import ArbolConstructor
from parsers.bc3_parser import BC3Parser
from utils.helpers import BC3Helpers
from utils.arbol_validator import ArbolValidator
from config.settings import settings

from typing import Optional
from pathlib import Path

import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bc3_import.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BC3ArbolOnlyReader:
    """Reader BC3 que únicamente guarda la estructura de árbol jerárquico"""

    def __init__(
        self,
        mongo_uri: str = None,
        database: str = None
    ):
        self.mongo_uri = mongo_uri or settings.MONGO_URI
        self.database = database or settings.MONGO_DATABASE
        self.connection: Optional[MongoDBConnection] = None
        self.parser = BC3Parser()
        self.arbol_constructor = ArbolConstructor()

    def importar_solo_arbol(
        self,
        filepath: str,
        exportar_arbol_json: bool = True,
        validar_arbol: bool = True,
        sobrescribir: bool = False
    ) -> bool:
        """
        Importa un archivo BC3 y guarda ÚNICAMENTE la estructura de árbol

        Args:
            filepath: Ruta al archivo BC3
            exportar_arbol_json: Si True, exporta estructura de árbol a JSON
            validar_arbol: Si True, valida la integridad del árbol construido
            sobrescribir: Si True, sobrescribe árbol existente

        Returns:
            True si la importación fue exitosa
        """
        try:
            # Verificar archivo
            if not Path(filepath).exists():
                logger.error(f"El archivo no existe: {filepath}")
                return False

            logger.info("=== INICIANDO IMPORTACIÓN BC3 - SOLO ÁRBOL ===")
            logger.info(f" Archivo: {filepath}")

            # Verificar si ya existe el árbol
            archivo_name = Path(filepath).name
            if not sobrescribir:
                with MongoDBConnection(self.mongo_uri, self.database) as conn:
                    repo_temp = BC3ArbolRepository(conn)
                    existente = repo_temp.verificar_arbol_existente(
                        archivo_name)

                    if existente.get('existe'):
                        logger.warning(
                            f" Ya existe un árbol para {archivo_name}")
                        logger.info(
                            f" Creado: {existente.get('fecha_creacion')}")
                        logger.info(f" Nodos: {existente.get('total_nodos')}")
                        logger.info(
                            " Use sobrescribir=True para reemplazarlo")
                        return False

            # Paso 1: Parsear archivo BC3
            logger.info(" Paso 1: Parseando archivo BC3...")
            datos = self.parser.parse_file(filepath)

            if not datos:
                logger.error(" No se pudieron parsear los datos del archivo")
                return False

            # Mostrar estadísticas de parseo (solo para info)
            stats_parseo = BC3Helpers.calcular_estadisticas(datos)
            logger.info(f" Estadísticas de parseo: {stats_parseo}")

            # Paso 2: Construir árbol jerárquico
            logger.info(" Paso 2: Construyendo árbol jerárquico...")
            arbol = self.arbol_constructor.construir_arbol(
                datos['conceptos'],
                datos['descomposiciones'],
                datos['mediciones']
            )

            # Mostrar estadísticas de construcción
            stats_construccion = (
                self.arbol_constructor.obtener_estadisticas_construccion())
            logger.info(
                "Estadísticas de construcción del árbol: "
                f"{stats_construccion}"
            )

            # Paso 3: Validar árbol (opcional)
            if validar_arbol:
                logger.info(" Paso 3: Validando integridad del árbol...")
                resultado_validacion = ArbolValidator.validar_arbol(arbol)

                if resultado_validacion['valido']:
                    logger.info(" Árbol válido - sin errores detectados")
                else:
                    logger.warning(" Árbol con problemas:")
                    for error in resultado_validacion['errores']:
                        logger.error(f"   ERROR: {error}")
                    for advertencia in resultado_validacion['advertencias']:
                        logger.warning(f"   ADVERTENCIA: {advertencia}")

            # Paso 4: Exportar a JSON (opcional)
            if exportar_arbol_json:
                arbol_json_path = f"{Path(filepath).stem}_arbol.json"
                self._exportar_arbol_json(arbol, str(arbol_json_path))

            # Paso 5: Conectar a MongoDB
            logger.info(" Paso 5: Conectando a MongoDB...")
            self.connection = MongoDBConnection(self.mongo_uri, self.database)

            if not self.connection.connect():
                logger.error(" No se pudo conectar a MongoDB")
                return False

            # Crear solo los índices necesarios para el árbol
            self._crear_indices_arbol()

            # Paso 6: Eliminar árbol existente si se solicita sobrescribir
            repository = BC3ArbolRepository(self.connection)
            if sobrescribir:
                logger.info(" Eliminando árbol existente...")
                repository.eliminar_arbol(archivo_name)

            # Paso 7: Guardar ÚNICAMENTE la estructura de árbol
            logger.info(
                " Paso 7: Guardando estructura de árbol en MongoDB...")

            # Establecer archivo origen
            arbol.archivo_origen = archivo_name

            # Guardar solo el árbol usando el método específico
            resultado_arbol = repository.save_solo_arbol(arbol)

            if resultado_arbol.get('error'):
                logger.error(
                    f" Error guardando árbol: {resultado_arbol['error']}")
                return False

            logger.info(" Estructura de árbol guardada:")
            logger.info(f"   Total nodos: {resultado_arbol['total_nodos']}")
            logger.info(f"   Nodos raíz: {resultado_arbol['nodos_raiz']}")
            logger.info(
                f"   Niveles máximos: {resultado_arbol['niveles_maximos']}")
            logger.info(
                f"   Importe total: {resultado_arbol['importe_total']}")

            # Paso 8: Verificación final
            logger.info(" Paso 8: Verificación final...")
            stats_finales = repository.calcular_estadisticas_arbol(
                archivo_name)
            logger.info(f" Estadísticas finales en BD: {stats_finales}")

            # Resumen final
            logger.info("===  IMPORTACIÓN DE ÁRBOL COMPLETADA ===")
            logger.info(" Resumen:")
            logger.info(f" Archivo: {Path(filepath).name}")
            logger.info(
                f" Nodos totales: {stats_finales.get('total_nodos', 0)}")
            logger.info(f" Nodos raíz: {stats_finales.get('nodos_raiz', 0)}")
            logger.info(
                f" Niveles: {stats_finales.get('nivel_maximo', 0) + 1}")
            logger.info(
                f" Mediciones: {stats_finales.get('total_mediciones', 0)}")
            logger.info(
                f" Importe total: €"
                f"{stats_finales.get('importe_total', 0):,.2f}")

            if validar_arbol and not resultado_validacion['valido']:
                logger.warning(" Importación completada con advertencias")
            else:
                logger.info(" Importación completada sin errores")

            return True

        except Exception as e:
            logger.error(f" Error durante la importación: {e}", exc_info=True)
            return False

        finally:
            if self.connection:
                self.connection.disconnect()

    def listar_arboles_disponibles(self) -> list:
        """
        Lista todos los árboles disponibles en la base de datos
        """
        try:
            with MongoDBConnection(self.mongo_uri, self.database) as conn:
                collection = conn.get_collection("metadata_arbol")
                if collection is None:
                    return []

                arboles = list(collection.find(
                    {'tipo_importacion': 'solo_arbol'},
                    {
                        'archivo_origen': 1,
                        'fecha_importacion': 1,
                        'total_nodos': 1,
                        'nodos_raiz': 1,
                        'niveles_maximos': 1,
                        'importe_total_presupuesto': 1
                    }
                ).sort('fecha_importacion', -1))

                return arboles

        except Exception as e:
            logger.error(f" Error listando árboles: {e}")
            return []

    def eliminar_arbol(self, archivo_origen: str) -> bool:
        """
        Elimina un árbol específico
        """
        try:
            with MongoDBConnection(self.mongo_uri, self.database) as conn:
                repository = BC3ArbolRepository(conn)
                return repository.eliminar_arbol(archivo_origen)

        except Exception as e:
            logger.error(f" Error eliminando árbol: {e}")
            return False

    def _crear_indices_arbol(self):
        """Crea únicamente los índices necesarios para el árbol"""
        try:
            # Índices para estructura del árbol
            arbol_col = self.connection.get_collection("arbol_conceptos")
            if arbol_col is not None:
                arbol_col.create_index("archivo_origen")
                arbol_col.create_index("tipo")
                arbol_col.create_index([("archivo_origen", 1), ("tipo", 1)])

            # Índices para nodos individuales
            nodos_col = self.connection.get_collection("nodos_arbol")
            if nodos_col is not None:
                nodos_col.create_index(
                    [("codigo", 1), ("archivo_origen", 1)], unique=True)
                nodos_col.create_index("codigo")
                nodos_col.create_index("archivo_origen")
                nodos_col.create_index("estructura.codigo_padre")
                nodos_col.create_index("estructura.nivel_jerarquico")
                nodos_col.create_index("estructura.es_raiz")
                nodos_col.create_index("estructura.es_hoja")
                nodos_col.create_index("concepto.tipo")
                nodos_col.create_index("concepto.es_capitulo")
                nodos_col.create_index("concepto.es_partida")

            # Índices para metadata del árbol
            metadata_col = self.connection.get_collection("metadata_arbol")
            if metadata_col is not None:
                metadata_col.create_index("archivo_origen")
                metadata_col.create_index("tipo_importacion")
                metadata_col.create_index("fecha_importacion")

            logger.info(" Índices del árbol creados exitosamente")

        except Exception as e:
            logger.error(f" Error creando índices del árbol: {e}")

    def _exportar_arbol_json(self, arbol, filepath: str):
        """Exporta la estructura del árbol a JSON"""
        try:
            estructura = arbol.obtener_estructura_json()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(estructura, f, indent=2,
                          ensure_ascii=False, default=str)

            logger.info(f" Estructura de árbol exportada a: {filepath}")

        except Exception as e:
            logger.error(f" Error exportando árbol a JSON: {e}")

    def obtener_estadisticas_archivo(self, filepath: str) -> dict:
        """
        Obtiene estadísticas del archivo sin guardarlo en BD
        """
        try:
            logger.info(f" Analizando archivo: {filepath}")

            # Parsear archivo
            datos = self.parser.parse_file(filepath)
            if not datos:
                return {}

            # Construir árbol
            arbol = self.arbol_constructor.construir_arbol(
                datos['conceptos'],
                datos['descomposiciones'],
                datos['mediciones']
            )

            # Compilar estadísticas
            stats = {
                'archivo': {
                    'nombre': Path(filepath).name,
                    'tamaño_mb': round((Path(filepath).stat()
                                        .st_size / 1024 / 1024, 2))
                },
                'parseo': BC3Helpers.calcular_estadisticas(datos),
                'arbol': (self.arbol_constructor
                          .obtener_estadisticas_construccion()),
                'validacion': ArbolValidator.validar_arbol(arbol)
            }

            return stats

        except Exception as e:
            logger.error(f" Error obteniendo estadísticas: {e}")
            return {}


if __name__ == '__main__':
    reader = BC3ArbolOnlyReader()
    reader.importar_solo_arbol('./data/prueba.bc3', sobrescribir=True)
