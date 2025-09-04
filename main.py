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


class BC3ArbolReader:
    """Reader BC3 con capacidades de construcción de árbol jerárquico"""

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

    def importar_archivo_con_arbol(
        self,
        filepath: str,
        exportar_json: bool = False,
        exportar_arbol_json: bool = True,
        validar_arbol: bool = True
    ) -> bool:
        """
        Importa un archivo BC3 a MongoDB construyendo también la
        estructura de árbol

        Args:
            filepath: Ruta al archivo BC3
            exportar_json: Si True, exporta datos planos a JSON
            exportar_arbol_json: Si True, exporta estructura de árbol a JSON
            validar_arbol: Si True, valida la integridad del árbol construido

        Returns:
            True si la importación fue exitosa
        """
        try:
            # Verificar archivo
            if not Path(filepath).exists():
                logger.error(f"El archivo no existe: {filepath}")
                return False

            logger.info("=== INICIANDO IMPORTACIÓN BC3 CON ÁRBOL ===")
            logger.info(f"Archivo: {filepath}")

            # Paso 1: Parsear archivo BC3
            logger.info("Paso 1: Parseando archivo BC3...")
            datos = self.parser.parse_file(filepath)

            if not datos:
                logger.error("No se pudieron parsear los datos del archivo")
                return False

            # Mostrar estadísticas de parseo
            stats_parseo = BC3Helpers.calcular_estadisticas(datos)
            logger.info(f"Estadísticas de parseo: {stats_parseo}")

            # Paso 2: Construir árbol jerárquico
            logger.info("Paso 2: Construyendo árbol jerárquico...")
            arbol = self.arbol_constructor.construir_arbol(
                datos['conceptos'],
                datos['descomposiciones'],
                datos['mediciones']
            )

            # Mostrar estadísticas de construcción
            stats_construccion = (
                self.arbol_constructor.obtener_estadisticas_construccion())
            logger.info(
                f"Estadísticas de construcción del árbol: {stats_construccion}"
            )

            # Paso 3: Validar árbol (opcional)
            if validar_arbol:
                logger.info("Paso 3: Validando integridad del árbol...")
                resultado_validacion = ArbolValidator.validar_arbol(arbol)

                if resultado_validacion['valido']:
                    logger.info(" Árbol válido - sin errores detectados")
                else:
                    logger.warning(" Árbol con problemas:")
                    for error in resultado_validacion['errores']:
                        logger.error(f"  ERROR: {error}")
                    for advertencia in resultado_validacion['advertencias']:
                        logger.warning(f"  ADVERTENCIA: {advertencia}")

            # Paso 4: Exportar a JSON (opcional)
            if exportar_json:
                json_path = Path(filepath).with_suffix('.json')
                BC3Helpers.exportar_a_json(datos, str(json_path))

            if exportar_arbol_json:
                arbol_json_path = f"{Path(filepath).stem}_arbol.json"
                self._exportar_arbol_json(arbol, str(arbol_json_path))

            # Paso 5: Conectar a MongoDB
            logger.info("Paso 5: Conectando a MongoDB...")
            self.connection = MongoDBConnection(self.mongo_uri, self.database)

            if not self.connection.connect():
                logger.error("No se pudo conectar a MongoDB")
                return False

            # Crear índices
            self.connection.create_indexes()

            # Paso 6: Guardar datos planos
            logger.info("Paso 6: Guardando datos planos en MongoDB...")
            repository = BC3ArbolRepository(self.connection)
            resultado_plano = repository.save_all(datos)

            logger.info("Datos planos guardados:")
            logger.info(
                f"  - Conceptos: {resultado_plano['conceptos_insertados']}")
            logger.info(
                "  - Descomposiciones: " +
                f"{resultado_plano['descomposiciones_insertadas']}")
            logger.info(
                f"  - Mediciones: {resultado_plano['mediciones_insertadas']}")
            logger.info(f"  - Textos: {resultado_plano['textos_insertados']}")

            # Paso 7: Guardar estructura de árbol
            logger.info("Paso 7: Guardando estructura de árbol en MongoDB...")
            arbol.archivo_origen = datos['metadata']['archivo']
            resultado_arbol = repository.save_arbol_completo(arbol)

            logger.info("Estructura de árbol guardada:")
            logger.info(f"  - Total nodos: {resultado_arbol['total_nodos']}")
            logger.info(f"  - Nodos raíz: {resultado_arbol['nodos_raiz']}")
            logger.info(
                f"  - Niveles máximos: {resultado_arbol['niveles_maximos']}")
            logger.info(
                f"  - Importe total: {resultado_arbol['importe_total']}")

            # Paso 8: Verificación final
            logger.info("Paso 8: Verificación final...")
            stats_finales = repository.calcular_estadisticas_arbol(
                datos['metadata']['archivo'])
            logger.info(f"Estadísticas finales en BD: {stats_finales}")

            # Resumen final
            logger.info("=== IMPORTACIÓN COMPLETADA EXITOSAMENTE ===")
            logger.info("Resumen:")
            logger.info(f"Archivo: {Path(filepath).name}")
            logger.info(
                f" Conceptos: {stats_finales.get('total_nodos', 0)}")
            logger.info(
                f" Nodos raíz: {stats_finales.get('nodos_raiz', 0)}")
            logger.info(
                f" Niveles: {stats_finales.get('nivel_maximo', 0) + 1}")
            logger.info(
                f" Mediciones: {stats_finales.get('total_mediciones', 0)}")
            logger.info(
                " Importe total: €"
                f"{stats_finales.get('importe_total', 0):,.2f}")

            if (resultado_plano['errores'] or
                    (validar_arbol and not resultado_validacion['valido'])):
                logger.warning(" Importación completada con advertencias")
            else:
                logger.info(" Importación completada sin errores")

            return True

        except Exception as e:
            logger.error(f"Error durante la importación: {e}", exc_info=True)
            return False

        finally:
            if self.connection:
                self.connection.disconnect()

    def consultar_arbol(
        self,
        archivo_origen: str = None
    ):
        """
        Proporciona herramientas de consulta del árbol guardado
        """
        try:
            self.connection = MongoDBConnection(self.mongo_uri, self.database)

            if not self.connection.connect():
                logger.error("No se pudo conectar a MongoDB para consultas")
                return None

            repository = BC3ArbolRepository(self.connection)

            return BC3ArbolConsultor(repository, archivo_origen)

        except Exception as e:
            logger.error(f"Error creando consultor: {e}")
            return None

    def _exportar_arbol_json(self, arbol, filepath: str):
        """Exporta la estructura del árbol a JSON"""
        try:
            estructura = arbol.obtener_estructura_json()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(estructura, f, indent=2,
                          ensure_ascii=False, default=str)

            logger.info(f"Estructura de árbol exportada a: {filepath}")

        except Exception as e:
            logger.error(f"Error exportando árbol a JSON: {e}")


class BC3ArbolConsultor:
    """Consultor para navegar y consultar el árbol de conceptos"""

    def __init__(
        self,
        repository: BC3ArbolRepository,
        archivo_origen: str = None
    ):
        self.repository = repository
        self.archivo_origen = archivo_origen

    def obtener_raices(self):
        """Obtiene todos los nodos raíz"""
        return self.repository.obtener_nodos_raiz(self.archivo_origen)

    def obtener_hijos(
        self,
        codigo_padre: str
    ):
        """Obtiene hijos directos de un nodo"""
        return self.repository.obtener_hijos_directos(
            codigo_padre, self.archivo_origen)

    def obtener_descendientes_completos(
        self,
        codigo_padre: str
    ):
        """Obtiene todos los descendientes de un nodo"""
        return self.repository.obtener_todos_descendientes(
            codigo_padre, self.archivo_origen)

    def obtener_ruta_completa(
        self,
        codigo: str
    ):
        """Obtiene la ruta completa desde la raíz hasta el nodo"""
        return self.repository.obtener_ruta_hasta_raiz(
            codigo, self.archivo_origen)

    def obtener_por_nivel(
        self,
        nivel: int
    ):
        """Obtiene todos los nodos de un nivel específico"""
        return self.repository.obtener_nodos_por_nivel(
            nivel, self.archivo_origen)

    def buscar_por_tipo(
        self,
        tipo: str
    ):
        """Busca nodos por tipo de concepto"""
        return self.repository.buscar_nodos_por_tipo(tipo, self.archivo_origen)

    def obtener_con_mediciones(self):
        """Obtiene nodos que tienen mediciones"""
        return self.repository.obtener_nodos_con_mediciones(
            self.archivo_origen)

    def obtener_nodo_detallado(
        self,
        codigo: str
    ):
        """Obtiene información detallada de un nodo"""
        nodo = self.repository.obtener_nodo(codigo, self.archivo_origen)

        if nodo:
            # Enriquecer con información adicional
            nodo['hijos_directos'] = self.obtener_hijos(codigo)
            nodo['ruta_completa'] = self.obtener_ruta_completa(codigo)

        return nodo

    def generar_reporte_arbol(
        self
    ) -> dict:
        """Genera un reporte completo del árbol"""
        stats = self.repository.calcular_estadisticas_arbol(
            self.archivo_origen)
        raices = self.obtener_raices()
        nodos_con_mediciones = self.obtener_con_mediciones()

        return {
            'estadisticas_generales': stats,
            'nodos_raiz': len(raices),
            'detalle_raices': [
                {
                    'codigo': r['codigo'],
                    'resumen': r.get('concepto', {}).get('resumen', ''),
                    'numero_hijos': (r.get('estructura', {})
                                     .get('numero_hijos', 0)),
                    'importe_total': (r.get('estadisticas', {})
                                      .get('importe_total_arbol'))
                }
                for r in raices
            ],
            'nodos_con_mediciones': len(nodos_con_mediciones),
            'archivo_origen': self.archivo_origen
        }

    def imprimir_arbol_completo(
        self,
        mostrar_mediciones: bool = False
    ):
        """Imprime la estructura completa del árbol en consola"""
        raices = self.obtener_raices()

        print(f"\n{'='*60}")
        print("ESTRUCTURA DE ÁRBOL - " +
              f"{self.archivo_origen or 'TODOS LOS ARCHIVOS'}")
        print(f"{'='*60}")

        for raiz in raices:
            self._imprimir_nodo_recursivo(
                raiz, nivel=0, mostrar_mediciones=mostrar_mediciones)

    def _imprimir_nodo_recursivo(
            self,
            nodo: dict,
            nivel: int = 0,
            mostrar_mediciones: bool = False):
        """Imprime un nodo y sus descendientes recursivamente"""
        indent = "  " * nivel
        concepto = nodo.get('concepto', {})
        estadisticas = nodo.get('estadisticas', {})

        # Información básica del nodo
        print(
            f"{indent}├─ [{concepto.get('codigo', 'N/A')}]" +
            f"{concepto.get('resumen', 'Sin resumen')}"
        )

        # Información adicional
        if concepto.get('precio'):
            print(f"{indent}   💰 Precio: €{concepto['precio']:,.2f}")

        if estadisticas.get('importe_total_arbol'):
            print(
                f"{indent}   💼 Total árbol: €" +
                f"{estadisticas['importe_total_arbol']:,.2f}"
            )

        if estadisticas.get('numero_mediciones', 0) > 0:
            print(
                f"{indent}   📐 Mediciones: " +
                f"{estadisticas['numero_mediciones']}"
            )

            if mostrar_mediciones:
                mediciones = nodo.get('mediciones', [])
                for med in mediciones[:3]:  # Mostrar solo las primeras 3
                    total = med.get('medicion_total', 0)
                    print(f"{indent}     └─ Total medición: {total}")
                if len(mediciones) > 3:
                    print(f"{indent}     └─ ... y {len(mediciones)-3} más")

        # Obtener e imprimir hijos
        hijos = self.obtener_hijos(concepto.get('codigo', ''))
        for hijo in hijos:
            self._imprimir_nodo_recursivo(hijo, nivel + 1, mostrar_mediciones)


if __name__ == '__main__':
    reader = BC3ArbolReader()
    reader.importar_archivo_con_arbol('./data/prueba.bc3')
