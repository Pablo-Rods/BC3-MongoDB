from models.base_model import BC3BaseModel

from decimal import Decimal
from typing import Optional
from pydantic import Field


class Concepto(BC3BaseModel):
    """Modelo para registrar los ~C"""

    codigo: str = Field(
        ...,
        description="Código del concepto",
        examples=["OUM1234, Cap1.1 #"]
    )

    unidad: Optional[str] = Field(
        None,
        description="Unidad de medida",
        examples=["m2"]
    )

    resumen: Optional[str] = Field(
        None,
        description="Resumen o breve descripción del concepto"
    )

    precio: Optional[Decimal] = Field(
        None,
        description="Precio unitario del concepto"
    )

    fecha: Optional[str] = Field(
        None,
        description="Fecha del precio"
    )

    tipo: Optional[str] = Field(
        None,
        description="Tipo del concepto, es un número del 0 al 5"
    )

    # TODO: ¿Son necesarios?
    # Propiedades derivadas
    es_capitulo: bool = Field(
        False,
        description="Indica si el concepto es un capítulo"
    )

    es_partida: bool = Field(
        False,
        description="Indica si el concepto es una partida"
    )

    nivel: Optional[int] = Field(
        None,
        description="Profundidad del concepto en el árbol jerarquico"
    )

    class Config:
        json_encoders = {
            **BC3BaseModel.Config.json_encoders,
            Decimal: lambda v: float(v)
        }

    # TODO: ¿Hay una mejor forma?
    def determinar_tipo(self):
        """Calcula las propiedades derivadas"""
        if self.tipo:
            tipo_num = int(self.tipo)
            self.es_capitulo = tipo_num in [0, 1]
            self.es_partida = tipo_num in [2, 3]

        if self.codigo:
            self.nivel = self.codigo.count("#") + 1
