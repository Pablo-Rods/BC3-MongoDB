from decimal import Decimal
from typing import Any

import logging

logger = logging.getLogger(__name__)


class BC3Validator:
    """Validador de los datos leidos"""

    @staticmethod
    def validar_codigo(
        codigo: str
    ) -> bool:
        if not codigo:
            return False

        codigo = codigo.strip()
        return len(codigo) > 0 and len(codigo) <= 20

    @staticmethod
    def validar_precio(
        precio: Any
    ) -> bool:
        # El precio es opcional
        if precio is None:
            return True

        try:
            precio_decimal = Decimal(str(precio))
            return precio_decimal >= 0
        except Exception:
            return False

    @staticmethod
    def validar_unidad(
        unidad: str
    ) -> bool:
        # La unidad es opcional
        if not unidad:
            return True

        unidades_validas = [
            'ud', 'u', 'm', 'm2', 'm3', 'kg', 't',
            'l', 'h', 'pa', 'ml', 'km', 'dia', '%'
        ]

        return unidad.lower() in unidades_validas

    @staticmethod
    def validar_tipo_concepto(
        tipo: str
    ) -> bool:
        # el tipo puede no estar definido
        if not tipo:
            return True

        try:
            tipo_num = int(tipo)
            return 0 <= tipo_num <= 5
        except Exception:
            return False
