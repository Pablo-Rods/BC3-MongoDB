from models.base_model import BC3BaseModel

from typing import Optional, List
from decimal import Decimal
from pydantic import Field


class LineaMedicion(BC3BaseModel):
    """Línea individual de medición"""

    tipo_linea: Optional[int] = Field(
        None,
        description="Tipo de línea. Es un valor entre 1 y 3"
    )

    comentario: Optional[str] = Field(
        None
    )

    unidades: Optional[Decimal] = Field(
        None
    )

    longitud: Optional[Decimal] = Field(
        None
    )

    latitud: Optional[Decimal] = Field(
        None
    )

    altura: Optional[Decimal] = Field(
        None
    )

    etiqueta: Optional[str] = Field(
        None,
    )

    parcial: Optional[Decimal] = Field(
        None
    )

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

    def calcular_parcial(self):
        if self.tipo_linea == 1:
            valores = [
                self.unidades or Decimal(1),
                self.longitud or Decimal(1),
                self.latitud or Decimal(1),
                self.altura or Decimal(1)
            ]
            self.parcial = Decimal(1)
            for v in valores:
                self.parcial *= v


class Medicion(BC3BaseModel):
    """Modelo para registrar los ~M"""

    codigo_padre: str = Field(
        ...,
        description="Código del concepto padre"
    )

    codigo_hijo: str = Field(
        ...,
        description="Código del concepto al que se aplica la medición"
    )

    posicion: Optional[List[int]] = Field(
        None,
        description="Posición del hijo en la descomposición"
    )

    medicion_total: Decimal = Field(
        None,
        description="Debe coincidir con el rendimiento del registro tipo" +
        "'~D' correspondiente."
    )

    lineas_medición: List[LineaMedicion] = Field(
        default_factory=list,
        description="Líneas de medición"
    )

    # TODO: ¿Son necesarios?

    numero_lineas: int = Field(
        0
    )

    def calcular_total(self):
        """Calcula las propiedades derivadas"""
        self.numero_lineas = len(self.lineas_medición)

        # total = Decimal(0)
        # for linea in self.lineas_medición:
        #     if linea.tipo_linea == 1 and linea.parcial:
        #         total += linea.parcial
        # self.total_medicion = total
