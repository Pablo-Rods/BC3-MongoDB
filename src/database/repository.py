from src.database.connection import MongoDBConnection
from src.models.descomposicion import Descomposicion
from src.models.texto import Texto, TextoPliego
from src.models.medicion import Medicion
from src.models.concepto import Concepto
from src.config.settings import settings

from typing import Dict, Any, List, Optional
from pymongo.errors import BulkWriteError
from datetime import datetime
from decimal import Decimal

import logging

logger = logging.getLogger(__name__)


class BC3Repository:
    """Repositorio para poder gestionar las querys"""

    def __init__(
        self,
        connection: MongoDBConnection
    ):
        self.connection = connection
        self.stats = {
            'conceptos_insertados': 0,
            'descomposiciones_insertadas': 0,
            'mediciones_insertadas': 0,
            'textos_insertados': 0,
            'errores': []
        }

    def save_all(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Guarda todos los datos parseados en MongoDB

        Args:
            data: Diccionario con todos los registros parseados

        Returns:
            Estadísticas de la operación
        """
        if not self.connection._is_connected():
            logger.error("No hay conexión a la base de datos")
            return self.stats

        # Guardar metadata
        if 'metadata' in data:
            self._save_metadata(data['metadata'])

        # Guardar conceptos
        if 'conceptos' in data and data['conceptos']:
            self._save_conceptos(data['conceptos'])

        # Guardar descomposiciones
        if 'descomposiciones' in data and data['descomposiciones']:
            self._save_descomposiciones(data['descomposiciones'])

        # Guardar mediciones
        if 'mediciones' in data and data['mediciones']:
            self._save_mediciones(data['mediciones'])

        # Guardar textos
        if 'textos' in data and data['textos']:
            self._save_textos(data['textos'])

        # Guardar textos de pliego
        if 'textos_pliego' in data and data['textos_pliego']:
            self._save_textos_pliego(data['textos_pliego'])

        return self.stats

    def buscar_concepto(
        self,
        codigo: str,
        archivo: str = None
    ) -> Optional[Dict]:
        """Busca un concepto por código"""
        collection = self.connection.get_collection(
            settings.COMCEPTOS_COLLECTION)
        if collection is None:
            return None

        filtro = {'codigo': codigo}
        if archivo:
            filtro['archivo_origen'] = archivo

        return collection.find_one(filtro)

    def buscar_descomposicion(
        self,
        codigo_padre: str
    ) -> List[Dict]:
        """Busca las descomposiciones de un concepto"""
        collection = self.connection.get_collection(
            settings.DESCOMPOSICIONES_COLLECTION)
        if not collection:
            return []

        return list(collection.find({'codigo_padre': codigo_padre}))

    # TODO: implementar
    def obtener_estructura_arbol(self, codigo_raiz: str = None) -> Dict:
        """Obtiene la estructura jerárquica del presupuesto"""
        pass

    def _save_metadata(self, metadata: Dict[str, Any]):
        """Guarda la metadata del archivo BC3"""
        try:
            collection = self.connection.get_collection(
                settings.METADATA_COLLECTION)
            if collection is None:
                return

            metadata['fecha_importacion'] = datetime.now()
            metadata['_id'] = (
                f"{metadata['archivo']}_{datetime.now().isoformat()}")

            metadata = self._convert_decimals(metadata)

            collection.insert_one(metadata)
            logger.info(
                f"Metadata guardada para archivo: {metadata['archivo']}")

        except Exception as e:
            logger.error(f"Error guardando metadata: {e}")
            self.stats['errores'].append(f"Metadata: {str(e)}")

    def _save_conceptos(self, conceptos: List[Concepto]):
        """Guarda los conceptos en batch"""
        collection = self.connection.get_collection(
            settings.CONCEPTOS_COLLECTION)
        if collection is None:
            return

        try:
            for concepto in conceptos:
                try:
                    doc = concepto.to_mongo()
                    # Asegurar conversión de Decimals
                    doc = self._convert_decimals(doc)

                    collection.update_one(
                        {'codigo': doc.get('codigo'),
                         'archivo_origen': doc.get(
                            'archivo_origen')},
                        {'$set': doc},
                        upsert=True
                    )
                    self.stats['conceptos_insertados'] += 1
                except Exception as e:
                    logger.warning(
                        f"Error insertando concepto {concepto.codigo}: {e}")

            logger.info(
                f"Insertados {self.stats['conceptos_insertados']} conceptos")

        except Exception as e:
            logger.error(f"Error guardando conceptos: {e}")
            self.stats['errores'].append(f"Conceptos: {str(e)}")

    def _save_descomposiciones(self, descomposiciones: List[Descomposicion]):
        """Guarda las descomposiciones en batch"""
        collection = self.connection.get_collection(
            settings.DESCOMPOSICIONES_COLLECTION)
        if collection is None:
            return

        try:
            documentos = []
            for desc in descomposiciones:
                doc = desc.to_mongo()
                # Asegurar conversión de Decimals
                doc = self._convert_decimals(doc)
                documentos.append(doc)

            if documentos:
                result = collection.insert_many(documentos, ordered=False)
                self.stats['descomposiciones_insertadas'] = len(
                    result.inserted_ids)
                logger.info(
                    f"Insertadas {self.stats['descomposiciones_insertadas']}" +
                    "descomposiciones")

        except BulkWriteError as e:
            # Algunos documentos pueden haberse insertado aunque haya errores
            self.stats['descomposiciones_insertadas'] = e.details.get(
                'nInserted', 0)
            logger.warning(
                f"Insertadas {self.stats['descomposiciones_insertadas']}" +
                "descomposiciones con errores")
        except Exception as e:
            logger.error(f"Error guardando descomposiciones: {e}")
            self.stats['errores'].append(f"Descomposiciones: {str(e)}")

    def _save_mediciones(self, mediciones: List[Medicion]):
        """Guarda las mediciones en batch"""
        collection = self.connection.get_collection(
            settings.MEDICIONES_COLLECTION)
        if collection is None:
            return

        try:
            documentos = []
            for med in mediciones:
                doc = med.to_mongo()
                # Asegurar conversión de Decimals
                doc = self._convert_decimals(doc)
                documentos.append(doc)

            if documentos:
                result = collection.insert_many(documentos, ordered=False)
                self.stats['mediciones_insertadas'] = len(result.inserted_ids)
                logger.info(
                    f"Insertadas {self.stats['mediciones_insertadas']}" +
                    "mediciones")

        except BulkWriteError as e:
            self.stats['mediciones_insertadas'] = e.details.get('nInserted', 0)
            logger.warning(
                f"Insertadas {self.stats['mediciones_insertadas']}" +
                "mediciones con errores")
        except Exception as e:
            logger.error(f"Error guardando mediciones: {e}")
            self.stats['errores'].append(f"Mediciones: {str(e)}")

    def _save_textos(self, textos: List[Texto]):
        """Guarda los textos en batch"""
        collection = self.connection.get_collection(settings.TEXTOS_COLLECTION)
        if collection is None:
            return

        try:
            documentos = [texto.to_mongo() for texto in textos]

            if documentos:
                # Usar upsert para evitar duplicados
                for doc in documentos:
                    try:
                        collection.update_one(
                            {'codigo': doc.get('codigo'),
                             'archivo_origen': doc.get(
                                'archivo_origen')},
                            {'$set': doc},
                            upsert=True
                        )
                        self.stats['textos_insertados'] += 1
                    except Exception as e:
                        logger.warning(
                            "Error insertando texto para" +
                            f"{doc.get('codigo')}: {e}")

                logger.info(
                    f"Insertados {self.stats['textos_insertados']} textos")

        except Exception as e:
            logger.error(f"Error guardando textos: {e}")
            self.stats['errores'].append(f"Textos: {str(e)}")

    def _save_textos_pliego(self, textos_pliego: List[TextoPliego]):
        """Guarda los textos de pliego"""
        collection = self.connection.get_collection(settings.TEXTOS_COLLECTION)
        if collection is None:
            return

        try:
            documentos = []
            for texto in textos_pliego:
                doc = texto.to_mongo()
                doc['es_pliego'] = True  # Marcar como pliego
                documentos.append(doc)

            if documentos:
                for doc in documentos:
                    try:
                        collection.update_one(
                            {'codigo': doc.get('codigo'), 'es_pliego': True},
                            {'$set': doc},
                            upsert=True
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error insertando texto de pliego: {e}")

        except Exception as e:
            logger.error(f"Error guardando textos de pliego: {e}")
            self.stats['errores'].append(f"Textos pliego: {str(e)}")

    def _convert_decimals(self, obj: Any) -> Any:
        """Convierte recursivamente todos los Decimal a float"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        return obj
