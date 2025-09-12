from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

import logging
import hashlib
import json
import re

logger = logging.getLogger(__name__)


class BC3Helpers:
    """Funciones auxiliares para el procesamiento BC3"""

    @staticmethod
    def generar_id_unico(codigo: str, archivo: str) -> str:
        """Genera un ID único para un registro"""
        texto = f"{codigo}_{archivo}_{datetime.now().isoformat()}"
        return hashlib.md5(texto.encode()).hexdigest()

    @staticmethod
    def limpiar_texto_rtf(texto: str) -> str:
        """Limpia texto en formato RTF"""
        if not texto:
            return ""

        # Eliminar marcadores RTF básicos
        texto = re.sub(r'\{\\rtf.*?\}', '', texto)
        texto = re.sub(r'\\[a-z]+\d*\s?', '', texto)
        texto = re.sub(r'[{}]', '', texto)

        return texto.strip()

    @staticmethod
    def formatear_importe(importe: Decimal) -> str:
        """Formatea un importe para mostrar"""
        return (f"{importe:,.2f}".replace(',', 'X')
                .replace('.', ',').replace('X', '.'))

    @staticmethod
    def exportar_a_json(data: Dict[str, Any], filepath: str):
        """Exporta los datos a un archivo JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Datos exportados a: {filepath}")
        except Exception as e:
            logger.error(f"Error exportando a JSON: {e}")

    @staticmethod
    def calcular_estadisticas(data: Dict[str, List]) -> Dict[str, Any]:
        """Calcula estadísticas sobre los datos parseados"""
        stats = {
            'total_conceptos': len(data.get('conceptos', [])),
            'total_descomposiciones': len(data.get('descomposiciones', [])),
            'total_mediciones': len(data.get('mediciones', [])),
            'total_textos': len(data.get('textos', [])),
            'capitulos': 0,
            'partidas': 0,
            'precios_nulos': 0,
            'importe_total': Decimal(0)
        }

        for concepto in data.get('conceptos', []):
            if concepto.es_capitulo:
                stats['capitulos'] += 1
            if concepto.es_partida:
                stats['partidas'] += 1
            if concepto.precio is None:
                stats['precios_nulos'] += 1
            elif concepto.precio:
                stats['importe_total'] += concepto.precio

        return stats
