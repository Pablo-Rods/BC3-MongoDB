from src.models.base_model import BC3BaseModel

from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import Field


class ComponenteDescomposicion(BC3BaseModel):
    # TODO: ¿Se puede hacer en  el global?
    """Modelo para registrar un elemento de la descomposición"""

    codigo_componente: str = Field(
        ...,
        description="Código del componente"
    )

    factor: Optional[Decimal] = Field(
        None,
        description="Factor de conversión o cantidad del componente"
    )

    rendimiento: Optional[Decimal] = Field(
        None,
        description="Utilización del concepto"
    )

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class Descomposicion(BC3BaseModel):
    """Modelo para registrar los ~D"""

    codigo_padre: str = Field(
        ...,
        description="Código del concepto padre"
    )

    componentes: List[ComponenteDescomposicion] = Field(
        default_factory=list,
        description="Lista de los componentes en los que" +
        "se descompone el padre"
    )

    # TODO: ¿Son necesarios?
    # Propiedades derivadas
    importe_total: Optional[Decimal] = Field(
        None,
        description="Sumatorio de los precios de los conceptos hijos"
    )

    numero_componetes: int = Field(
        0,
        description="Número de conceptos hijos"
    )

    # TODO: Posiblemente dará problemas de rendimiento debido al
    # anidamiento de for/ ifs
    def calcular_totales(
        self,
        precios_unitarios: Dict[str, Decimal]
    ):
        """Calcula las propiedades derivadas"""
        self.numero_componetes = len(self.componentes)

        if precios_unitarios:
            total = Decimal(0)
            for c in self.componentes:
                if c.codigo_componente in precios_unitarios:
                    precio = precios_unitarios[c.codigo_componente]
                    factor = c.factor or Decimal(1)
                    total += precio * factor
            self.importe_total = total
