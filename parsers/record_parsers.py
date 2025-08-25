from models.descomposicion import Descomposicion, ComponenteDescomposicion
from models.medicion import Medicion, LineaMedicion
from models.texto import Texto, TextoPliego
from models.concepto import Concepto
from config.settings import settings

from decimal import Decimal, InvalidOperation
from typing import Optional

import logging

logger = logging.getLogger(__name__)


class RecordParser:
    """Parsea cada una de las lineas o registros del BC3"""

    def parse_concepto(
        self,
        record: str,
        archivo_origen: str = None
    ) -> Optional[Concepto]:
        """
        Parsea un registro ~C
        Formato: ~C|CODIGO|UNIDAD|RESUMEN|PRECIO|FECHA|TIPO|
        """
        try:
            fields = record.split(settings.FIELD_SEPARATOR)

            if len(fields) < 3:
                return None

            concepto = Concepto(
                codigo=(self.__clean_field(fields[1])
                        if len(fields) > 1 else None),
                unidad=(self.__clean_field(fields[2])
                        if len(fields) > 2 else None),
                resumen=(self.__clean_field(fields[3])
                         if len(fields) > 3 else None),
                archivo_origen=archivo_origen
            )

            if len(fields) > 4 and fields[4]:
                concepto.precio = self.__parse_decimal(fields[4])

            if len(fields) > 5 and fields[5]:
                concepto.fecha = self.__clean_field(fields[5])

            if len(fields) > 6 and fields[6]:
                concepto.tipo = self.__clean_field(fields[6])

            return concepto

        except Exception as e:
            logger.error(f"Error parseando concepto: {e}")
            return None

    def parse_descomposicion(
        self,
        record: str,
        archivo_origen: str = None
    ) -> Optional[Descomposicion]:
        """
        Parsea un registro ~D
        Formato: ~D|CODIGO_PADRE|CODIGO_HIJO|FACTOR|RENDIMIENTO|...
        """
        try:
            fields = record.split(settings.FIELD_SEPARATOR)

            if len(fields) < 3:
                return None

            descomposion = Descomposicion(
                codigo_padre=self.__clean_field(fields[1]),
                archivo_origen=archivo_origen
            )

            i = 2
            while i < len(fields) - 1:
                codigo = self.__clean_field(fields[i])
                if not codigo:
                    break

                componente = ComponenteDescomposicion(
                    codigo_componente=codigo,
                    archivo_origen=archivo_origen
                )

                if i + 1 < len(fields) and fields[i + 1]:
                    componente.factor = self.__parse_decimal(
                        fields[i + 1])

                if i + 2 < len(fields) and fields[i + 2]:
                    componente.rendimiento = self.__parse_decimal(
                        fields[i + 2])

                descomposion.componentes.append(componente)
                i += 3

            return descomposion

        except Exception as e:
            logger.error(f"Error parseando descomposición: {e}")
            return None

    def parse_medicion(
        self,
        record: str,
        archivo_origen: str = None
    ) -> Optional[Medicion]:
        """
        Parsea un registro ~M
        Formato ~M|CODIGO_PADRE|CODIGO_HIJO|POSICION|LINEAS_MEDICION|
        """
        try:
            fields = record.split(settings.FIELD_SEPARATOR)

            if len(fields) < 4:
                return None

            medicion = Medicion(
                codigo_padre=self.__clean_field(fields[1]),
                codigo_hijo=self.__clean_field(fields[2]),
                archivo_origen=archivo_origen
            )

            if fields[3]:
                try:
                    medicion.posicion = int(fields[3])
                except ValueError:
                    pass

            if len(fields) > 4 and fields[4]:
                lineas_texto = fields[4]
                # Cada \\ simboliza un cambio de línea
                lineas = lineas_texto.split('\\')

                for linea_texto in lineas:
                    linea = self.__parse_linea_medicion(
                        linea_texto, archivo_origen)
                    if linea:
                        medicion.lineas_medición.append(linea)

            return Medicion

        except Exception as e:
            logger.error(f"Error parseando medición: {e}")
            return None

    def parse_texto(
        self,
        record: str,
        archivo_origen: str = None
    ) -> Optional[Texto]:
        """
        Parsea un registro ~T
        Formato: ~T|CODIGO|TEXTO|
        """
        try:
            fields = record.split(settings.FIELD_SEPARATOR)

            if len(fields) < 3:
                return None

            texto = Texto(
                codigo=self.__clean_field(fields[1]),
                texto=self.__clean_field(fields[2]) if len(fields) > 2 else "",
                archivo_origen=archivo_origen
            )

            return texto

        except Exception as e:
            logger.error(f"Error parseando texto: {e}")
            return None

    def parse_text0_pliego(
        self,
        record: str,
        archivo_origen: str = None
    ) -> Optional[TextoPliego]:
        """
        Parsea un registro ~X
        Formato: ~X|CODIGO|TEXTO_PLIEGO|TIPO
        """
        try:
            fields = record.split(settings.FIELD_SEPARATOR)

            if len(fields) < 3:
                return None

            texto_pliego = TextoPliego(
                codigo=self.__clean_field(fields[1]),
                texto_pliego=self.__clean_field(fields[2])
                if len(fields) > 2 else "",
                archivo_origen=archivo_origen
            )

            if len(fields) > 3:
                texto_pliego.tipo_pliego = self.__clean_field(fields[3])

            texto_pliego.contar_articulos()
            return texto_pliego

        except Exception as e:
            logger.error(f"Error parseando texto de pliego: {e}")
            return None

    def __parse_linea_medicion(
        self,
        linea_texto: str,
        archivo_origen: str = None
    ) -> Optional[LineaMedicion]:
        """
        Parsea una línea individual de medición
        Formato: tipo|comentario|unidades|longitud|anchura|altura|
        """
        try:
            partes = linea_texto.split('|')

            if not partes:
                return None

            linea = LineaMedicion(
                archivo_origen=archivo_origen
                )

            if len(partes) > 0 and partes[0]:
                try:
                    linea.tipo_linea = int(partes[0])
                except ValueError:
                    linea.tipo_linea = 1

            if len(partes) > 1:
                linea.comentario = self.__clean_field(partes[1])

            campos_numericos = ['unidades', 'longitud', 'anchura', 'altura']
            for i, campo in enumerate(campos_numericos, start=2):
                if len(partes) > i and partes[i]:
                    valor = self.__parse_decimal(partes[i])
                    if valor:
                        setattr(linea, campo, valor)

            linea.calcular_parcial()
            return linea

        except Exception as e:
            logger.warning(f"Error parseando línea de medición: {e}")
            return None

    def __clean_field(
        self,
        field: str
    ) -> Optional[str]:
        "Limpia y normaliza un campo de un registro"
        if not field:
            return None

        field = field.strip()

        field = field.removeprefix('\\\\', '\\')
        field = field.replace('\\n', '\n')
        field = field.replace('\\t', '\\')

        return field if field else None

    def __parse_decimal(
        self,
        value: str
    ) -> Optional[Decimal]:
        """Convierte un string a Decimal"""
        if not value:
            return None

        try:
            value = value.strip()
            value = value.replace(',', '.')
            value = value.replace(' ', '')

            return Decimal(value)

        except (InvalidOperation, ValueError):
            logger.warning(f"No se pudo convertir '{value}' a Decimal")
            return None
