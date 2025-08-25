from models.descomposicion import Descomposicion
from parsers.record_parsers import RecordParser
from models.texto import Texto, TextoPliego
from models.medicion import Medicion
from models.concepto import Concepto
from config.settings import settings

from typing import List, Any, Dict
from pathlib import Path

import logging
import re

logger = logging.getLogger(__name__)


class BC3PARSER:
    """Lee el BC3 al completo"""

    def __init__(
        self,
        encoding: str = None
    ):
        self.metadata: Dict[str, Any]
        self.textos: List[Texto] = []
        self.conceptos: List[Concepto] = []
        self.record_parser = RecordParser()
        self.mediciones: List[Medicion] = []
        self.textos_pliegos: List[TextoPliego] = []
        self.descomposiciones: List[Descomposicion] = []
        self.encoding = encoding or settings.DEFAULT_ENCODING

    def parse_file(
        self,
        filepath: str
    ) -> Dict[str, List]:
        """
        Parsea un archivo BC3 a nuestro modelo de datos

        Args:
            filepath: Ruta al archivo .bc3

        Returns:
            Diccionario con todos los registros parseados
        """
        logger.info(f"Iniciando parseo del archivo: {filepath}")

        try:
            content = self.__read_file(filepath)

            self.metadata = self.__extract_metadata(filepath, content)

            records = self.__split_records(content)

            for record in records:
                self.__process_record(record)

            self.__post_process()

            logger.info(f"Parseo completado. Conceptos: {len(self.conceptos)},"
                        f"Descomposiciones: {len(self.descomposiciones)},"
                        f"Mediciones: {len(self.mediciones)},"
                        f"Textos: {len(self.textos)}")

            return {
                'metadata': self.metadata,
                'conceptos': self.conceptos,
                'descomposiciones': self.descomposiciones,
                'mediciones': self.mediciones,
                'textos': self.textos,
                'textos_pliego': self.textos_pliego
            }

        except Exception as e:
            logger.error(f"Error parseando archivo: {e}")
            raise

    def __read_file(
        self,
        filepath: str
    ) -> str:
        """
        Lee el contenido del archivo BC3
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(
                "El archivo seleccionado parece no existir"
                )

        try:
            with open(filepath, 'r', encoding=self.encoding) as f:
                return f.read()

        except UnicodeDecodeError:
            for enc in ['latin-1', 'utf-80', 'cp850']:
                try:
                    with open(filepath, 'r', encoding=enc) as f:
                        logger.info(f"Archivo leído con encoding: {enc}")
                        return f.read()

                except UnicodeError:
                    continue
            raise ValueError("No se pudo determinar el encoding del archivo")

    def __extract_metadata(
        self,
        filepath: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Extrae metadata del archivo .bc3
        """
        metadata = {
            'archivo': Path(filepath).name,
            'tamaño_bytes': Path(filepath).stat().st_size,
            'version_bc3': None,
            'programa_origen': None,
            'fecha_generacion': None
        }

        version_match = re.search(r'~V\|([^|]*)\|', content)
        programa_match = re.search(r'~K\|([^|]*)\|([^|]*)\|([^|]*)\|', content)

        if version_match:
            metadata['version_bc3'] = version_match.group(1)

        if programa_match:
            metadata['programa_origen'] = programa_match.group(1)
            metadata['version_programa'] = programa_match.group(2)
            metadata['fecha_generacion'] = programa_match.group(3)

        return metadata

    def __split_records(
        self,
        content: str
    ) -> List[str]:
        """
        Dicide el contenido del BC3 en registros individuales
        """
        records = re.split(r'(?=~[A-Z])', content)
        return [r.strip() for r in records if r.split()]

    def __process_record(
        self,
        record: str
    ):
        """
        Procesa un registro individual del BC3 según su tipo
        """
        if not record or len(record) < 2:
            return

        record_type = record[1] if record[0] == "~" else None

        if not record_type:
            return

        try:
            if record_type == 'C':
                self.__process_concepto(record)
            elif record_type == "D":
                self.__process_descomposicion(record)
            elif record_type == "M":
                self.__process_medicion(record)
            elif record_type == "T":
                self.__process_texto(record)
            elif record_type == "X":
                self.__process_texto_pliego(record)

        except Exception as e:
            logger.warning("Error procesando registro tipo"
                           f"{record_type}: {e}")

    def __process_concepto(
        self,
        record: str
    ):
        concepto = self.record_parser.parse_concepto(
            record, self.metadata.get('archivo')
        )
        if concepto:
            self.conceptos.append(concepto)

    def __process_descomposicion(
        self,
        record: str
    ):
        descomposicion = self.record_parser.parse_descomposicion(
            record, self.metadata.get('archivo')
        )
        if descomposicion:
            self.descomposiciones.append(descomposicion)

    def __process_medicion(
        self,
        record: str
    ):
        medicion = self.record_parser.parse_medicion(
            record, self.metadata.get('archivo')
        )
        if medicion:
            self.mediciones.append(medicion)

    def __process_texto(
        self,
        record: str
    ):
        texto = self.record_parser.parse_texto(
            record, self.metadata.get('archivo')
        )
        if texto:
            self.textos.append(texto)

    def __process_texto_pliego(
        self,
        record: str
    ):
        texto_pliego = self.record_parser.parse_texto_pliego(
            record, self.metadata.get('archivo')
        )
        if texto_pliego:
            self.textos_pliegos.append(texto_pliego)

    def __post_process(self):
        precios = {c.codigo: c.precio for c in self.conceptos if c.precio}

        for desc in self.descomposiciones:
            desc.calcular_totales(precios)

        for med in self.mediciones:
            med.calcular_total()

        for texto in self.textos:
            texto.procesar_texto()

        for con in self.conceptos:
            con.determinar_tipo()
