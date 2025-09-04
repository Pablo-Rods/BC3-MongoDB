from models.arbol_conceptos import ArbolConceptos

from typing import Dict, List


class ArbolValidator:
    """Validador para verificar la integridad del árbol construido"""

    @staticmethod
    def validar_arbol(
        arbol: ArbolConceptos
    ) -> Dict[str, any]:
        """Valida la integridad del árbol construido"""
        errores = []
        advertencias = []

        # Verificar referencias circulares
        circulares = ArbolValidator._detectar_referencias_circulares(arbol)
        if circulares:
            errores.extend(
                [f"Referencia circular detectada: {ref}"
                 for ref in circulares])

        # Verificar huérfanos
        huerfanos = ArbolValidator._detectar_huerfanos(arbol)
        if huerfanos:
            advertencias.extend(
                [f"Nodo huérfano (sin padre ni hijos): {codigo}"
                 for codigo in huerfanos])

        # Verificar consistencia de niveles
        inconsistencias_nivel = ArbolValidator._verificar_consistencia_niveles(
            arbol)
        if inconsistencias_nivel:
            advertencias.extend(
                [f"Inconsistencia de nivel: {inc}"
                 for inc in inconsistencias_nivel])

        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'advertencias': advertencias,
            'estadisticas': {
                'nodos_validados': len(arbol.nodos),
                'referencias_circulares': len(circulares),
                'huerfanos': len(huerfanos),
                'inconsistencias_nivel': len(inconsistencias_nivel)
            }
        }

    @staticmethod
    def _detectar_referencias_circulares(
        arbol: ArbolConceptos
    ) -> List[str]:
        """Detecta referencias circulares en el árbol"""
        circulares = []

        def tiene_ciclo(
            codigo: str,
            visitados: set,
            ruta_actual: list
        ) -> bool:
            if codigo in visitados:
                if codigo in ruta_actual:
                    idx = ruta_actual.index(codigo)
                    ciclo = ' → '.join(ruta_actual[idx:] + [codigo])
                    circulares.append(ciclo)
                    return True
                return False

            visitados.add(codigo)
            ruta_actual.append(codigo)

            if codigo in arbol.nodos:
                for hijo in arbol.nodos[codigo].codigos_hijos:
                    if tiene_ciclo(hijo, visitados, ruta_actual):
                        return True

            ruta_actual.remove(codigo)
            return False

        visitados = set()
        for codigo_raiz in arbol.nodos_raiz:
            if codigo_raiz not in visitados:
                tiene_ciclo(codigo_raiz, visitados, [])

        return circulares

    @staticmethod
    def _detectar_huerfanos(
        arbol: ArbolConceptos
    ) -> List[str]:
        """Detecta nodos huérfanos (sin padre ni hijos)"""
        huerfanos = []

        for codigo, nodo in arbol.nodos.items():
            if nodo.codigo_padre is None and nodo.numero_hijos == 0:
                # Es huérfano si no está en la lista de raíces explícitas
                if codigo not in arbol.nodos_raiz:
                    huerfanos.append(codigo)

        return huerfanos

    @staticmethod
    def _verificar_consistencia_niveles(
        arbol: ArbolConceptos
    ) -> List[str]:
        """Verifica que los niveles jerárquicos sean consistentes"""
        inconsistencias = []

        for codigo, nodo in arbol.nodos.items():
            if nodo.codigo_padre:
                if nodo.codigo_padre in arbol.nodos:
                    padre = arbol.nodos[nodo.codigo_padre]
                    nivel_esperado = padre.nivel_jerarquico + 1

                    if nodo.nivel_jerarquico != nivel_esperado:
                        inconsistencias.append(
                            f"{codigo}: nivel {nodo.nivel_jerarquico}, "
                            f"esperado {nivel_esperado}" +
                            f"(padre: {nodo.codigo_padre})"
                        )

        return inconsistencias
