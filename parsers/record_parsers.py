from models.descomposicion import Descomposicion, ComponenteDescomposicion
from models.medicion import Medicion, LineaMedicion
from models.texto import Texto, TextoPliego
from models.concepto import Concepto
from config.settings import settings

from decimal import Decimal, InvalidOperation
from typing import Optional, List

import logging
import re

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

            componentes = fields[2].split('\\')
            i = 0
            while i < len(componentes) - 1:
                codigo = self.__clean_field(componentes[i])
                if not codigo:
                    break

                componente = ComponenteDescomposicion(
                    codigo_componente=codigo,
                    archivo_origen=archivo_origen
                )

                if i + 1 < len(componentes) and componentes[i + 1]:
                    componente.factor = self.__parse_decimal(
                        componentes[i + 1])

                if i + 2 < len(componentes) and componentes[i + 2]:
                    componente.rendimiento = self.__parse_decimal(
                        componentes[i + 2])

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
        try:
            fields = record.split(settings.FIELD_SEPARATOR)

            if len(fields) < 3:
                return None

            # Campo 1: [CODIGO_PADRE\]CODIGO_HIJO
            codigos_field = fields[1]
            if '\\' in codigos_field:
                # Tiene código padre
                codigos = codigos_field.split('\\')
                codigo_padre = self.__clean_field(codigos[0])
                codigo_hijo = self.__clean_field(
                    codigos[1]) if len(codigos) > 1 else None
            else:
                # Solo código hijo (mediciones no estructuradas)
                codigo_padre = None
                codigo_hijo = self.__clean_field(codigos_field)

            medicion = Medicion(
                codigo_padre=codigo_padre,
                codigo_hijo=codigo_hijo,
                archivo_origen=archivo_origen
            )

            # Campo 2: {POSICION\} - opcional
            if len(fields) > 2 and fields[2]:
                posiciones = fields[2].split("\\")
                medicion.posicion = []
                for p in posiciones:
                    try:
                        pos_num = int(p.strip())
                        if pos_num > 0:  # Las posiciones empiezan en 1
                            medicion.posicion.append(pos_num)
                    except ValueError:
                        pass

            # Campo 3: MEDICION_TOTAL
            if len(fields) > 3 and fields[3]:
                medicion.medicion_total = self.__parse_decimal(fields[3])

            # Campo 4: {TIPO\COMENTARIO{#ID_BIM}\UNIDADES\
            # LONGITUD\LATITUD\ALTURA\} - líneas de medición
            if len(fields) > 4 and fields[4]:
                lineas_medicion = self.__parse_lineas_medicion(
                    fields[4], archivo_origen)
                medicion.lineas_medición = lineas_medicion

            # Campo 5: [ETIQUETA] - opcional
            if len(fields) > 5 and fields[5]:
                medicion.etiqueta = self.__clean_field(fields[5])

            return medicion

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

    def parse_texto_pliego(
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

    def __parse_lineas_medicion(
        self,
        campo_medicion: str,
        archivo_origen: str = None
    ) -> List[LineaMedicion]:
        lineas = []

        if not campo_medicion:
            return lineas

        try:
            partes = campo_medicion.split('\\')

            i = 0
            while i < len(partes):
                # Necesitamos al menos 6 campos para una línea completa
                if i + 5 >= len(partes):
                    break

                linea = LineaMedicion(archivo_origen=archivo_origen)

                # TIPO - campo 0
                tipo_str = partes[i].strip()
                if tipo_str:
                    try:
                        linea.tipo_linea = int(tipo_str)
                    except ValueError:
                        linea.tipo_linea = None

                # COMENTARIO{#ID_BIM} - campo 1
                comentario_field = partes[i + 1]
                if comentario_field:
                    # Extraer ID_BIM si existe (#ID_BIM)
                    id_bim_match = re.search(r'#([^#]+)#', comentario_field)
                    if id_bim_match:
                        linea.id_bim = id_bim_match.group(1)
                        # Limpiar el comentario removiendo el ID_BIM
                        linea.comentario = re.sub(
                            r'#[^#]+#', '', comentario_field).strip()
                    else:
                        linea.comentario = self.__clean_field(comentario_field)

                # UNIDADES - campo 2
                if i + 2 < len(partes):
                    linea.unidades = self.__parse_decimal(partes[i + 2])

                # LONGITUD - campo 3
                if i + 3 < len(partes):
                    linea.longitud = self.__parse_decimal(partes[i + 3])

                # LATITUD - campo 4
                if i + 4 < len(partes):
                    linea.latitud = self.__parse_decimal(partes[i + 4])

                # ALTURA - campo 5
                if i + 5 < len(partes):
                    linea.altura = self.__parse_decimal(partes[i + 5])

                # Calcular el parcial según el tipo de línea
                self.__calcular_parcial_linea(linea)

                lineas.append(linea)

                # Avanzar al siguiente grupo de campos (6 campos por línea)
                i += 6

        except Exception as e:
            logger.warning(f"Error parseando líneas de medición: {e}")

        return lineas

    def __calcular_parcial_linea(self, linea: LineaMedicion):
        """
        Calcula el parcial de una línea de medición según su tipo
        """
        if linea.tipo_linea == 1:  # Línea normal - multiplicar dimensiones
            valores = [
                linea.unidades or Decimal('1'),
                linea.longitud or Decimal('1'),
                linea.latitud or Decimal('1'),
                linea.altura or Decimal('1')
            ]

            parcial = Decimal('1')
            for valor in valores:
                if valor is not None and valor != Decimal('0'):
                    parcial *= valor

            # Solo asignar si hay al menos un valor distinto de 1
            if any(v != Decimal('1') for v in valores if v is not None):
                linea.parcial = parcial

        elif linea.tipo_linea == 3:  # Expresión algebraica
            # Para expresiones, el parcial se evalúa
            # según la expresión en el comentario
            # Aquí podríamos implementar un evaluador
            #  de expresiones si fuera necesario
            linea.parcial = linea.unidades or Decimal('0')

        # Para tipos 1 (subtotal parcial) y 2 (subtotal acumulado),
        # el parcial se calcula a nivel superior según las líneas anteriores

    def __clean_field(
        self,
        field: str
    ) -> Optional[str]:
        """Limpia y normaliza un campo de un registro"""
        if not field:
            return None

        field = field.strip()

        # Decodificar secuencias de escape BC3
        field = field.replace('\\\\', '\\')
        field = field.replace('\\n', '\n')
        field = field.replace('\\t', '\t')

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

            # Normalizar separadores decimales
            value = value.replace(',', '.')
            value = value.replace(' ', '')

            # Remover caracteres no numéricos excepto punto y signo negativo
            value = re.sub(r'[^\d\.\-]', '', value)

            if value:
                return Decimal(value)
            else:
                return None

        except (InvalidOperation, ValueError):
            logger.warning(f"No se pudo convertir '{value}' a Decimal")
            return None
