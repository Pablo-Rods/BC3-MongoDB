from models.base_model import BC3BaseModel

from typing import Optional
from pydantic import Field


class Texto(BC3BaseModel):
    """Modelo para registrar los ~T"""

    codigo: str = Field(
        ...,
        description="Código del concepto al que pertenece el texto"
    )

    texto: str = Field(
        ...
    )

    tipo_texto: Optional[str] = Field(
        None
    )

    # TODO: ¿Son necesarios?
    # Propiedades derivadas
    longitud_texto: int = Field(
        0
    )

    tiene_formato: bool = Field(
        False,
        description="Indica si el texto tiene algún tipo de formato especial"
    )

    def procesar_texto(self):
        """Limpia la línea para quedarnos con el texto"""
        if self.texto:
            # Pasamos de formato BC3 a uno que entienda la DB
            self.texto = self.texto.replace('\\', '\n')
            self.texto = self.texto.strip()
            self.longitud_texto = len(self.texto)

            # Autodetectamos el encoding
            self.tiene_formato = (
                self.texto.startswith('{\\rtf}') or
                '<html>' in self.texto.lower()
            )


class TextoPliego(BC3BaseModel):
    """Modelo para registrar los ~T (Pliego de condiciones)"""

    codigo: str = Field(
        ...,
        description="Código del concepto al que pertenece el texto"
    )

    texto_pliego: str = Field(
        ...
    )

    tipo_pliego: Optional[str] = Field(
        None
    )

    # TODO: ¿Son necesarios?
    # Propiedades derivadas
    numero_artículos: int = Field(
        0
    )

    # TODO: Tengo serias dudas sobre esta funcionalidad
    def contar_articulos(self):
        if self.texto_pliego:
            self.numero_artículos = self.texto_pliego.lower().count('articulo')
