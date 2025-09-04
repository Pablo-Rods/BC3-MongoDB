from models.arbol_conceptos import ArbolConceptos
from database.connection import MongoDBConnection
from database.repository import BC3Repository

from typing import Dict, Any, Optional, List
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class BC3ArbolRepository(BC3Repository):
    """Extensión del repositorio para manejar árboles de conceptos"""

    def __init__(
        self,
        connection: MongoDBConnection
    ):
        super().__init__(connection)
        self.ARBOL_COLLECTION = "arbol_conceptos"

    def save_arbol_completo(
        self,
        arbol: ArbolConceptos
    ) -> Dict[str, Any]:
        """
        Guarda el árbol completo en MongoDB

        Args:
            arbol: Árbol de conceptos construido

        Returns:
            Estadísticas de la operación
        """
        if not self.connection._is_connected():
            logger.error("No hay conexión a la base de datos")
            return {'error': 'No hay conexión'}

        try:
            # Guardar estructura del árbol
            resultado_arbol = self._save_estructura_arbol(arbol)

            # Guardar nodos individuales para consultas rápidas
            resultado_nodos = self._save_nodos_individuales(arbol)

            # Crear índices específicos para el árbol
            self._crear_indices_arbol()

            stats = {
                'arbol_guardado': resultado_arbol['success'],
                'nodos_guardados': resultado_nodos['nodos_guardados'],
                'total_nodos': len(arbol.nodos),
                'nodos_raiz': len(arbol.nodos_raiz),
                'niveles_maximos': arbol.niveles_maximos,
                'importe_total': (float(arbol.importe_total_presupuesto)
                                  if arbol.importe_total_presupuesto else None)
            }

            logger.info(f"Árbol guardado exitosamente: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error guardando árbol: {e}")
            return {'error': str(e)}

    def _save_estructura_arbol(
        self,
        arbol: ArbolConceptos
    ) -> Dict[str, Any]:
        """Guarda la estructura completa del árbol"""
        try:
            collection = self.connection.get_collection(self.ARBOL_COLLECTION)
            if not collection:
                return {
                    'success': False,
                    'error': 'No se pudo acceder a la colección'
                }

            # Preparar documento del árbol completo
            documento_arbol = {
                '_id': (f"arbol_{arbol.archivo_origen}_" +
                        f"{datetime.now().isoformat()}"),
                'archivo_origen': arbol.archivo_origen,
                'fecha_creacion': datetime.now(),
                'metadata': {
                    'total_nodos': arbol.total_nodos,
                    'niveles_maximos': arbol.niveles_maximos,
                    'importe_total_presupuesto': (float(
                        arbol.importe_total_presupuesto
                    )if arbol.importe_total_presupuesto else None),
                    'nodos_raiz': arbol.nodos_raiz
                },
                'estructura_json': arbol.obtener_estructura_json(),
                'nodos_por_nivel': ({str(k): v for k, v
                                     in arbol.nodos_por_nivel.items()})
            }

            # Convertir decimales
            documento_arbol = self._convert_decimals(documento_arbol)

            # Guardar
            result = collection.update_one(
                {
                    'archivo_origen': arbol.archivo_origen,
                    'tipo': 'estructura_completa'
                },
                {'$set': {**documento_arbol, 'tipo': 'estructura_completa'}},
                upsert=True
            )

            return {
                'success': True,
                'upserted': result.upserted_id is not None,
                'modified': result.modified_count > 0
            }

        except Exception as e:
            logger.error(f"Error guardando estructura del árbol: {e}")
            return {'success': False, 'error': str(e)}

    def _save_nodos_individuales(
        self,
        arbol: ArbolConceptos
    ) -> Dict[str, Any]:
        """Guarda nodos individuales para consultas rápidas"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return {
                    'nodos_guardados': 0,
                    'error': 'No se pudo acceder a la colección'
                }

            nodos_guardados = 0

            for codigo, nodo in arbol.nodos.items():
                try:
                    # Preparar documento del nodo
                    doc_nodo = {
                        'codigo': codigo,
                        'archivo_origen': nodo.archivo_origen,
                        'concepto': nodo.concepto.dict(),
                        'estructura': {
                            'codigo_padre': nodo.codigo_padre,
                            'codigos_hijos': nodo.codigos_hijos,
                            'nivel_jerarquico': nodo.nivel_jerarquico,
                            'ruta_completa': nodo.ruta_completa,
                            'tiene_hijos': nodo.tiene_hijos,
                            'numero_hijos': nodo.numero_hijos,
                            'es_raiz': nodo.es_raiz(),
                            'es_hoja': nodo.es_hoja()
                        },
                        'mediciones': [med.dict() for med in nodo.mediciones],
                        'estadisticas': {
                            'numero_mediciones': nodo.numero_mediciones,
                            'medicion_total': (float(nodo.medicion_total)
                                               if nodo.medicion_total
                                               else None
                                               ),
                            'importe_propio': (float(nodo.importe_propio)
                                               if nodo.importe_propio
                                               else None
                                               ),
                            'importe_total_arbol': (
                                float(nodo.importe_total_arbol)
                                if nodo.importe_total_arbol
                                else None
                            )
                        },
                        'ruta_string': nodo.get_path_string(),
                        'fecha_actualizacion': datetime.now()
                    }

                    # Convertir decimales
                    doc_nodo = self._convert_decimals(doc_nodo)

                    # Guardar nodo
                    collection.update_one(
                        {
                            'codigo': codigo,
                            'archivo_origen': nodo.archivo_origen
                        },
                        {'$set': doc_nodo},
                        upsert=True
                    )

                    nodos_guardados += 1

                except Exception as e:
                    logger.warning(f"Error guardando nodo {codigo}: {e}")

            return {'nodos_guardados': nodos_guardados}

        except Exception as e:
            logger.error(f"Error guardando nodos individuales: {e}")
            return {'nodos_guardados': 0, 'error': str(e)}

    def _crear_indices_arbol(self):
        """Crea índices específicos para las colecciones del árbol"""
        try:
            # Índices para estructura del árbol
            arbol_col = self.connection.get_collection(self.ARBOL_COLLECTION)
            if arbol_col:
                arbol_col.create_index("archivo_origen")
                arbol_col.create_index("tipo")
                arbol_col.create_index([("archivo_origen", 1), ("tipo", 1)])

            # Índices para nodos individuales
            nodos_col = self.connection.get_collection("nodos_arbol")
            if nodos_col:
                nodos_col.create_index("codigo", unique=True)
                nodos_col.create_index("archivo_origen")
                nodos_col.create_index([("codigo", 1), ("archivo_origen", 1)])
                nodos_col.create_index("estructura.codigo_padre")
                nodos_col.create_index("estructura.nivel_jerarquico")
                nodos_col.create_index("estructura.es_raiz")
                nodos_col.create_index("estructura.es_hoja")
                nodos_col.create_index("concepto.tipo")
                nodos_col.create_index("concepto.es_capitulo")
                nodos_col.create_index("concepto.es_partida")

            logger.info("Índices del árbol creados exitosamente")

        except Exception as e:
            logger.error(f"Error creando índices del árbol: {e}")

    # Métodos de consulta del árbol

    def obtener_arbol_completo(
        self,
        archivo_origen: str = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene la estructura completa del árbol"""
        try:
            collection = self.connection.get_collection(self.ARBOL_COLLECTION)
            if not collection:
                return None

            filtro = {'tipo': 'estructura_completa'}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            return collection.find_one(filtro, sort=[('fecha_creacion', -1)])

        except Exception as e:
            logger.error(f"Error obteniendo árbol completo: {e}")
            return None

    def obtener_nodo(
        self,
        codigo: str,
        archivo_origen: str = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene un nodo específico"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return None

            filtro = {'codigo': codigo}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            return collection.find_one(filtro)

        except Exception as e:
            logger.error(f"Error obteniendo nodo {codigo}: {e}")
            return None

    def obtener_hijos_directos(
        self,
        codigo_padre: str,
        archivo_origen: str = None
    ) -> List[Dict[str, Any]]:
        """Obtiene los hijos directos de un nodo"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return []

            filtro = {'estructura.codigo_padre': codigo_padre}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            return list(collection.find(filtro).sort('concepto.codigo', 1))

        except Exception as e:
            logger.error(f"Error obteniendo hijos de {codigo_padre}: {e}")
            return []

    def obtener_nodos_raiz(
        self,
        archivo_origen: str = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los nodos raíz"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return []

            filtro = {'estructura.es_raiz': True}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            return list(collection.find(filtro).sort('concepto.codigo', 1))

        except Exception as e:
            logger.error(f"Error obteniendo nodos raíz: {e}")
            return []

    def obtener_nodos_por_nivel(
        self,
        nivel: int,
        archivo_origen: str = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los nodos de un nivel específico"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return []

            filtro = {'estructura.nivel_jerarquico': nivel}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            return list(collection.find(filtro).sort('concepto.codigo', 1))

        except Exception as e:
            logger.error(f"Error obteniendo nodos de nivel {nivel}: {e}")
            return []

    def buscar_nodos_por_tipo(
        self,
        tipo_concepto: str,
        archivo_origen: str = None
    ) -> List[Dict[str, Any]]:
        """Busca nodos por tipo de concepto"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return []

            filtro = {'concepto.tipo': tipo_concepto}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            return list(collection.find(filtro).sort('concepto.codigo', 1))

        except Exception as e:
            logger.error(f"Error buscando nodos tipo {tipo_concepto}: {e}")
            return []

    def obtener_ruta_hasta_raiz(
        self,
        codigo: str,
        archivo_origen: str = None
    ) -> List[Dict[str, Any]]:
        """Obtiene la ruta desde un nodo hasta la raíz"""
        try:
            nodo_actual = self.obtener_nodo(codigo, archivo_origen)
            if not nodo_actual:
                return []

            ruta = [nodo_actual]

            # Recorrer hacia arriba hasta la raíz
            while nodo_actual.get('estructura', {}).get('codigo_padre'):
                codigo_padre = nodo_actual['estructura']['codigo_padre']
                nodo_padre = self.obtener_nodo(codigo_padre, archivo_origen)

                if not nodo_padre:
                    break

                ruta.append(nodo_padre)
                nodo_actual = nodo_padre

            return list(reversed(ruta))  # Ruta desde raíz hasta nodo

        except Exception as e:
            logger.error(f"Error obteniendo ruta para {codigo}: {e}")
            return []

    def obtener_todos_descendientes(
        self,
        codigo_padre: str,
        archivo_origen: str = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los descendientes de un nodo (recursivo)"""
        try:
            descendientes = []

            # Obtener hijos directos
            hijos_directos = self.obtener_hijos_directos(
                codigo_padre, archivo_origen)
            descendientes.extend(hijos_directos)

            # Obtener descendientes de cada hijo recursivamente
            for hijo in hijos_directos:
                codigo_hijo = hijo.get('codigo')
                if codigo_hijo:
                    nietos = self.obtener_todos_descendientes(
                        codigo_hijo, archivo_origen)
                    descendientes.extend(nietos)

            return descendientes

        except Exception as e:
            logger.error(
                f"Error obteniendo descendientes de {codigo_padre}: {e}")
            return []

    def obtener_nodos_con_mediciones(
        self,
        archivo_origen: str = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los nodos que tienen mediciones asociadas"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return []

            filtro = {'estadisticas.numero_mediciones': {'$gt': 0}}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            return list(collection.find(filtro).sort('concepto.codigo', 1))

        except Exception as e:
            logger.error(f"Error obteniendo nodos con mediciones: {e}")
            return []

    def calcular_estadisticas_arbol(
        self,
        archivo_origen: str = None
    ) -> Dict[str, Any]:
        """Calcula estadísticas del árbol guardado"""
        try:
            collection = self.connection.get_collection("nodos_arbol")
            if not collection:
                return {}

            filtro = {}
            if archivo_origen:
                filtro['archivo_origen'] = archivo_origen

            pipeline = [
                {'$match': filtro},
                {'$group': {
                    '_id': None,
                    'total_nodos': {
                        '$sum': 1
                    },
                    'nodos_raiz': {
                        '$sum': {
                            '$cond': ['$estructura.es_raiz', 1, 0]
                        }
                    },
                    'nodos_hoja': {
                        '$sum': {
                            '$cond': ['$estructura.es_hoja', 1, 0]
                        }
                    },
                    'nodos_con_mediciones': {
                        '$sum': {
                            '$cond': [{
                                '$gt': ['$estadisticas.numero_mediciones', 0]
                            }, 1, 0]
                        }
                    },
                    'total_mediciones': {
                        '$sum': '$estadisticas.numero_mediciones'
                    },
                    'importe_total': {
                        '$sum': '$estadisticas.importe_total_arbol'
                    },
                    'nivel_maximo': {
                        '$max': '$estructura.nivel_jerarquico'
                    }
                }}
            ]

            resultado = list(collection.aggregate(pipeline))

            if resultado:
                stats = resultado[0]
                del stats['_id']
                return stats

            return {}

        except Exception as e:
            logger.error(f"Error calculando estadísticas del árbol: {e}")
            return {}
