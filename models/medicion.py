from models.base_model import BC3BaseModel

from typing import Optional, List
from decimal import Decimal
from pydantic import Field


class LineaMedicion(BC3BaseModel):
    """Línea individual de medición"""

    tipo_linea: Optional[int] = Field(
        None,
        description="Tipo de línea: 1=Normal, 2=Subtotal parcial, 3=Subtotal acumulado, 4=Expresión"
    )

    comentario: Optional[str] = Field(
        None,
        description="Comentario o expresión algebraica"
    )

    id_bim: Optional[str] = Field(
        None,
        description="Identificador BIM del elemento constructivo"
    )

    unidades: Optional[Decimal] = Field(
        None,
        description="Número de unidades"
    )

    longitud: Optional[Decimal] = Field(
        None,
        description="Longitud en metros"
    )

    latitud: Optional[Decimal] = Field(
        None,
        description="Anchura/Latitud en metros"
    )

    altura: Optional[Decimal] = Field(
        None,
        description="Altura en metros"
    )

    parcial: Optional[Decimal] = Field(
        None,
        description="Resultado del cálculo de la línea"
    )

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

    def calcular_parcial(self):
        """
        Calcula el parcial según el tipo de línea
        """
        if self.tipo_linea == 1 or self.tipo_linea is None:  # Línea normal
            # Multiplicar todas las dimensiones que existan
            valores = []

            if self.unidades is not None and self.unidades != Decimal('0'):
                valores.append(self.unidades)

            if self.longitud is not None and self.longitud != Decimal('0'):
                valores.append(self.longitud)

            if self.latitud is not None and self.latitud != Decimal('0'):
                valores.append(self.latitud)

            if self.altura is not None and self.altura != Decimal('0'):
                valores.append(self.altura)

            if valores:
                self.parcial = Decimal('1')
                for valor in valores:
                    self.parcial *= valor
            else:
                self.parcial = Decimal('0')

        elif self.tipo_linea == 3:  # Expresión algebraica
            # Para expresiones, normalmente se usa solo el campo unidades
            # o se evalúa la expresión en el comentario
            self.parcial = self.unidades or Decimal('0')


class Medicion(BC3BaseModel):
    """Modelo para registrar los ~M"""

    codigo_padre: Optional[str] = Field(
        None,
        description="Código del concepto padre (opcional para mediciones no estructuradas)"
    )

    codigo_hijo: str = Field(
        ...,
        description="Código del concepto al que se aplica la medición"
    )

    posicion: Optional[List[int]] = Field(
        None,
        description="Posición del hijo en la estructura jerárquica"
    )

    medicion_total: Optional[Decimal] = Field(
        None,
        description="Total de la medición, debe coincidir con el rendimiento en ~D"
    )

    etiqueta: Optional[str] = Field(
        None,
        description="Etiqueta o identificador del concepto para listados"
    )

    lineas_medición: List[LineaMedicion] = Field(
        default_factory=list,
        description="Líneas individuales de medición"
    )

    # Campos calculados
    numero_lineas: int = Field(
        0,
        description="Número de líneas de medición"
    )

    total_calculado: Optional[Decimal] = Field(
        None,
        description="Total calculado sumando las líneas de medición"
    )

    def calcular_total(self):
        """
        Calcula las propiedades derivadas
        """
        self.numero_lineas = len(self.lineas_medición)

        # Calcular el total sumando las líneas normales
        total = Decimal('0')
        for linea in self.lineas_medición:
            # Solo sumar líneas normales (tipo 1 o None) y expresiones (tipo 3)
            if linea.tipo_linea in [None, 1, 3] and linea.parcial:
                total += linea.parcial

        self.total_calculado = total

        # Si no hay medicion_total establecido, usar el calculado
        if self.medicion_total is None:
            self.medicion_total = total
