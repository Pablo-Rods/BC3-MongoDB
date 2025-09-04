from models.arbol_conceptos import ArbolConceptos, NodoConcepto
from models.descomposicion import Descomposicion
from models.medicion import Medicion
from models.concepto import Concepto

from typing import Dict, Set, List
from collections import defaultdict

import logging

logger = logging.getLogger(__name__)


class ArbolConstructor:
    """Construye el árbol de conceptos"""

    def __init__(self):
        self.arbol = ArbolConceptos()
        self.relaciones_padre_hijo: Dict[str, Set[str]] = defaultdict(set)
        self.mediciones_por_concepto: Dict[str,
                                           List[Medicion]] = defaultdict(list)

    def construir_arbol(
        self,
        conceptos: List[Concepto],
        descomposiciones: List[Descomposicion],
        mediciones: List[Medicion],
    ) -> ArbolConceptos:
        """
        Construye el árbol completo de conceptos

        Args:
            conceptos: Lista de conceptos
            descomposiciones: Lista de descomposiciones
            mediciones: Lista de mediciones

        Returns:
            Árbol completo de conceptos
        """
        logger.info("Construyendo árbol de conceptos...")

        self._crear_nodos(conceptos)
        self._procesar_descomposiciones(descomposiciones)
        self._detectar_jerarquia_por_codigo(conceptos)
        self._asociar_mediciones(mediciones)
        self._construir_estructura_final()
        self.arbol.calcular_importes_arbol()

        logger.info(f"Árbol construido: {self.arbol.total_nodos} nodos, "
                    f"{len(self.arbol.nodos_raiz)} raíces, "
                    f"{self.arbol.niveles_maximos + 1} niveles")

        return self.arbol

    def obtener_estadisticas_construccion(
        self
    ) -> Dict[str, int]:
        """Obtiene estadísticas del proceso de construcción"""
        stats = {
            'total_nodos': len(self.arbol.nodos),
            'nodos_raiz': len(self.arbol.nodos_raiz),
            'relaciones_padre_hijo': sum(
                len(hijos) for hijos
                in self.relaciones_padre_hijo.values()
            ),
            'niveles_maximos': self.arbol.niveles_maximos,
            'nodos_con_mediciones': sum(
                1 for nodo in self.arbol.nodos.values()
                if nodo.numero_mediciones > 0
            ),
            'nodos_hoja': sum(
                1 for nodo in self.arbol.nodos.values()
                if nodo.es_hoja()
            ),
            'total_mediciones': sum(
                nodo.numero_mediciones for nodo
                in self.arbol.nodos.values()
            )
        }

        return stats

    def _crear_nodos(
        self,
        conceptos: List[Concepto]
    ):
        """CXrea un nodo para cada concepto"""
        for concepto in conceptos:
            nodo = NodoConcepto(
                concepto=concepto,
                archivo_origen=concepto.archivo_origen
            )
            self.arbol.agregar_nodo(nodo)

        logger.info(f"Creados {len(conceptos)} nodos")

    def _procesar_descomposiciones(
        self,
        descomposiciones: List[Descomposicion]
    ):
        """Establece las relaciones padre-hijo"""
        relaciones = 0

        for desc in descomposiciones:
            codigo_padre = desc.codigo_padre

            for com in desc.componentes:
                codigo_hijo = com.codigo_componente

                if (codigo_hijo in self.arbol.nodos and
                        codigo_padre in self.arbol.nodos):
                    self.relaciones_padre_hijo[codigo_padre].add(codigo_hijo)
                    relaciones += 1

        logger.info(f"Procesadas {len(descomposiciones)} descomposiciones, "
                    f"encontradas {relaciones} relaciones")

    def _detectar_jerarquia_por_codigo(self, conceptos: List[Concepto]):
        """
        Detecta jerarquía por estructura de códigos
        (ej: Cap1, Cap1.1, Cap1.1.1)
        """
        # Agrupar conceptos por tipo para identificar jerarquías
        capitulos_por_nivel = defaultdict(list)

        for concepto in conceptos:
            if concepto.es_capitulo or concepto.tipo in ['0', '1']:
                # Detectar nivel por la estructura del código
                nivel = self._detectar_nivel_por_codigo(concepto.codigo)
                capitulos_por_nivel[nivel].append(concepto)

        # Establecer relaciones jerárquicas
        for nivel in sorted(capitulos_por_nivel.keys()):
            for concepto in capitulos_por_nivel[nivel]:
                padre_codigo = self._encontrar_padre_por_codigo(
                    concepto.codigo,
                    capitulos_por_nivel[nivel - 1] if nivel > 0 else []
                )

                if padre_codigo:
                    self.relaciones_padre_hijo[padre_codigo].add(
                        concepto.codigo)

        logger.info("Detectada jerarquía por código en" +
                    f"{len(capitulos_por_nivel)} niveles")

    def _detectar_nivel_por_codigo(
        self,
        codigo: str
    ) -> int:
        """Detecta el nivel jerárquico por la estructura del código"""
        # Contar puntos para códigos tipo "Cap1.1.1"
        if '.' in codigo:
            return codigo.count('.')

        # Contar # para códigos tipo "###"
        if '#' in codigo:
            return codigo.count('#')

        # Detectar por prefijos comunes
        if any(prefix in codigo.lower() for prefix in [
                'cap', 'subcap', 'apartado']):
            # Análisis más sofisticado si es necesario
            return 0

        return 0

    def _encontrar_padre_por_codigo(
        self,
        codigo_hijo: str,
        conceptos_nivel_superior: List[Concepto]
    ) -> str:
        """Encuentra el padre más probable por estructura de código"""
        if not conceptos_nivel_superior:
            return None

        # Para códigos con puntos (ej: 1.1.1 → padre es 1.1)
        if '.' in codigo_hijo:
            partes = codigo_hijo.split('.')
            if len(partes) > 1:
                codigo_padre_esperado = '.'.join(partes[:-1])

                # Buscar concepto con este código
                for concepto in conceptos_nivel_superior:
                    if concepto.codigo == codigo_padre_esperado:
                        return concepto.codigo

                # Buscar por prefijo más similar
                for concepto in conceptos_nivel_superior:
                    if codigo_hijo.startswith(concepto.codigo + '.'):
                        return concepto.codigo

        return None

    def _asociar_mediciones(
        self,
        mediciones: List[Medicion]
    ):
        """Asocia mediciones a sus conceptos correspondientes"""
        mediciones_asociadas = 0

        for medicion in mediciones:
            # Medición asociada directamente al código hijo
            codigo_concepto = medicion.codigo_hijo

            if codigo_concepto in self.arbol.nodos:
                self.arbol.agregar_medicion_a_concepto(
                    codigo_concepto, medicion)
                mediciones_asociadas += 1

            # Si tiene código padre, también podemos crear una asociación
            if (medicion.codigo_padre and medicion.codigo_padre
                    in self.arbol.nodos):
                # Esta medición también podría ser relevante para el padre
                # pero evitamos duplicados
                pass

        logger.info(f"Asociadas {mediciones_asociadas} mediciones a conceptos")

    def _construir_estructura_final(self):
        """Construye la estructura final del árbol"""
        # Establecer todas las relaciones padre-hijo
        for codigo_padre, codigos_hijos in self.relaciones_padre_hijo.items():
            for codigo_hijo in codigos_hijos:
                self.arbol.establecer_ralacion_padre_hijo(
                    codigo_padre, codigo_hijo)

        # Identificar y marcar nodos raíz
        self._identificar_raices()

        # Calcular propiedades de todos los nodos
        for nodo in self.arbol.nodos.values():
            nodo.calcular_propiedades()

        logger.info(f"Estructura final: {len(self.arbol.nodos_raiz)}" +
                    "raíces identificadas")

    def _identificar_raices(self):
        """Identifica los nodos raíz (sin padre)"""
        # Limpiar lista de raíces existente
        self.arbol.nodos_raiz.clear()

        # Todos los hijos conocidos
        todos_los_hijos = set()
        for hijos in self.relaciones_padre_hijo.values():
            todos_los_hijos.update(hijos)

        # Los nodos que no son hijos de nadie son raíces
        for codigo, nodo in self.arbol.nodos.items():
            if codigo not in todos_los_hijos:
                self.arbol.nodos_raiz.append(codigo)
                nodo.codigo_padre = None
                nodo.nivel_jerarquico = 0
                nodo.ruta_completa = []
