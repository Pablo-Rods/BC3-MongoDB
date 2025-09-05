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

        # Reinicializar el árbol para cada construcción
        self.arbol = ArbolConceptos()
        self.relaciones_padre_hijo = defaultdict(set)
        self.mediciones_por_concepto = defaultdict(list)

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
        """Crea un nodo para cada concepto"""
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
        """Establece las relaciones padre-hijo desde las descomposiciones"""
        relaciones = 0

        for desc in descomposiciones:
            codigo_padre = desc.codigo_padre

            # Verificar que el padre existe
            if codigo_padre not in self.arbol.nodos:
                logger.warning(
                    f"Padre {codigo_padre} no encontrado en conceptos")
                continue

            for componente in desc.componentes:
                codigo_hijo = componente.codigo_componente

                # Verificar que el hijo existe
                if codigo_hijo not in self.arbol.nodos:
                    logger.warning(
                        f"Hijo {codigo_hijo} no encontrado en conceptos")
                    continue

                # Establecer relación
                self.relaciones_padre_hijo[codigo_padre].add(codigo_hijo)
                relaciones += 1

                logger.debug(f"Relación: {codigo_padre} -> {codigo_hijo}")

        logger.info(f"Procesadas {len(descomposiciones)} descomposiciones, "
                    f"encontradas {relaciones} relaciones válidas")

        # Debug: Mostrar algunas relaciones para verificar
        if logger.isEnabledFor(logging.DEBUG):
            for padre, hijos in list(self.relaciones_padre_hijo.items())[:5]:
                logger.debug(f"  {padre} tiene hijos: {list(hijos)}")

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

        relaciones_jerarquicas = 0

        # Establecer relaciones jerárquicas
        for nivel in sorted(capitulos_por_nivel.keys()):
            if nivel == 0:
                continue  # Los de nivel 0 son raíces

            for concepto in capitulos_por_nivel[nivel]:
                padre_codigo = self._encontrar_padre_por_codigo(
                    concepto.codigo,
                    capitulos_por_nivel[nivel - 1] if nivel > 0 else []
                )

                if padre_codigo:
                    self.relaciones_padre_hijo[padre_codigo].add(
                        concepto.codigo)
                    relaciones_jerarquicas += 1
                    logger.debug(
                        f"Jerarquía por código: {padre_codigo} ->"
                        f"{concepto.codigo}"
                    )

        logger.info("Detectada jerarquía por código: " +
                    f"{relaciones_jerarquicas} relaciones en"
                    f"{len(capitulos_por_nivel)} niveles"
                    )

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
        logger.info("Construyendo estructura final del árbol...")

        # Debug: Mostrar cuántas relaciones tenemos
        total_relaciones = sum(len(hijos) for hijos
                               in self.relaciones_padre_hijo.values())
        logger.info(
            f"Total de relaciones padre-hijo a procesar: {total_relaciones}")

        # Establecer todas las relaciones padre-hijo
        relaciones_establecidas = 0
        for codigo_padre, codigos_hijos in self.relaciones_padre_hijo.items():
            logger.debug(
                f"Procesando padre {codigo_padre} con"
                f"{len(codigos_hijos)} hijos"
            )

            for codigo_hijo in codigos_hijos:
                # Verificar que ambos nodos existen antes de
                # establecer la relación
                if (
                    codigo_padre in self.arbol.nodos and
                    codigo_hijo in self.arbol.nodos
                ):
                    exito = self.arbol.establecer_relacion_padre_hijo(
                        codigo_padre, codigo_hijo)
                    if exito:
                        relaciones_establecidas += 1
                        logger.debug(
                            f"  Relación establecida: {codigo_padre}"
                            f" -> {codigo_hijo}"
                        )
                    else:
                        logger.warning(
                            f"  Relación rechazada (circular): {codigo_padre}"
                            f" -> {codigo_hijo}"
                        )
                else:
                    logger.warning(
                        f"  No se pudo establecer relación {codigo_padre} ->"
                        f" {codigo_hijo}: nodos no encontrados"
                    )

        logger.info(
            f"Relaciones padre-hijo establecidas: {relaciones_establecidas}")

        # Identificar y marcar nodos raíz
        self._identificar_raices()

        # Calcular propiedades de todos los nodos
        for codigo, nodo in self.arbol.nodos.items():
            nodo.calcular_propiedades()

        # Debug: Mostrar algunos nodos con hijos para verificar
        nodos_con_hijos = 0
        for codigo, nodo in self.arbol.nodos.items():
            if nodo.tiene_hijos:
                nodos_con_hijos += 1
                if nodos_con_hijos <= 5:  # Mostrar solo los primeros 5
                    logger.debug(
                        f"Nodo {codigo} tiene {nodo.numero_hijos} hijos:"
                        f" {nodo.codigos_hijos}"
                    )

        logger.info(f"Estructura final: {len(self.arbol.nodos_raiz)} "
                    "raíces identificadas, {nodos_con_hijos} nodos con hijos"
                    )

    def _identificar_raices(self):
        """Identifica los nodos raíz (sin padre)"""
        # Limpiar lista de raíces existente
        self.arbol.nodos_raiz.clear()

        # Todos los hijos conocidos
        todos_los_hijos = set()
        for hijos in self.relaciones_padre_hijo.values():
            todos_los_hijos.update(hijos)

        logger.debug(
            f"Total de nodos que son hijos de alguien: {len(todos_los_hijos)}")

        # Los nodos que no son hijos de nadie son raíces
        for codigo, nodo in self.arbol.nodos.items():
            if codigo not in todos_los_hijos:
                self.arbol.nodos_raiz.append(codigo)
                nodo.codigo_padre = None
                nodo.nivel_jerarquico = 0
                nodo.ruta_completa = []

        logger.info(f"Identificadas {len(self.arbol.nodos_raiz)} raíces")

        # Debug: Mostrar algunas raíces
        if logger.isEnabledFor(logging.DEBUG) and self.arbol.nodos_raiz:
            for i, raiz in enumerate(self.arbol.nodos_raiz[:5]):
                nodo_raiz = self.arbol.nodos[raiz]
                logger.debug(
                    f"  Raíz {i+1}: {raiz} - "
                    f"{(nodo_raiz.concepto.resumen[:50]
                        if nodo_raiz.concepto.resumen else 'Sin resumen')}")
